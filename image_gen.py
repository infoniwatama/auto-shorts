"""画像入手パイプライン
優先順位:
  1. assets/entities/<entity>.png  （ユーザー手配）
  2. Unsplash API 検索（無料・商用OK・帰属明記）
  3. Pexels API 検索（無料・商用OK・帰属明記）
  4. FLUX 1.1 Pro Ultra 生成（$0.06/枚）

config.IMAGE_BACKEND で 4 のバックエンドを切替（comfyui / flux_replicate）。
"""
import os
import time
import uuid
import urllib.parse
from pathlib import Path

import requests
from dotenv import load_dotenv

import config
import web_image_search

load_dotenv(config.ROOT / ".env")


# ============================================================
# ComfyUI バックエンド
# ============================================================

def _comfy_build_workflow(prompt: str, negative: str, seed: int) -> dict:
    return {
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "seed": seed,
                "steps": config.SD_STEPS,
                "cfg": config.SD_CFG,
                "sampler_name": config.SD_SAMPLER,
                "scheduler": config.SD_SCHEDULER,
                "denoise": 1.0,
                "model": ["4", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["5", 0],
            },
        },
        "4": {"class_type": "CheckpointLoaderSimple",
              "inputs": {"ckpt_name": config.SD_CHECKPOINT}},
        "5": {"class_type": "EmptyLatentImage",
              "inputs": {"width": config.SD_WIDTH, "height": config.SD_HEIGHT,
                         "batch_size": 1}},
        "6": {"class_type": "CLIPTextEncode",
              "inputs": {"text": prompt, "clip": ["4", 1]}},
        "7": {"class_type": "CLIPTextEncode",
              "inputs": {"text": negative, "clip": ["4", 1]}},
        "8": {"class_type": "VAEDecode",
              "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
        "9": {"class_type": "SaveImage",
              "inputs": {"filename_prefix": "auto_shorts", "images": ["8", 0]}},
    }


def _comfy_queue_prompt(workflow: dict, client_id: str) -> str:
    r = requests.post(
        f"{config.COMFYUI_HOST}/prompt",
        json={"prompt": workflow, "client_id": client_id},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["prompt_id"]


def _comfy_wait(prompt_id: str, timeout: float = 300) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        r = requests.get(f"{config.COMFYUI_HOST}/history/{prompt_id}", timeout=10)
        r.raise_for_status()
        history = r.json()
        if prompt_id in history:
            return history[prompt_id]
        time.sleep(0.5)
    raise TimeoutError(f"ComfyUI prompt {prompt_id} timed out")


def _comfy_download_image(image_info: dict, out_path: Path) -> None:
    params = {
        "filename": image_info["filename"],
        "type": image_info["type"],
        "subfolder": image_info.get("subfolder", ""),
    }
    url = f"{config.COMFYUI_HOST}/view?" + urllib.parse.urlencode(params)
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    out_path.write_bytes(r.content)


def _generate_image_comfyui(prompt: str, out_path: Path, genre,
                              seed: int | None = None) -> Path:
    if seed is None:
        seed = int(uuid.uuid4().int % (2**32))
    full_prompt = genre.SD_STYLE_PREFIX + prompt + genre.SD_STYLE_SUFFIX
    workflow = _comfy_build_workflow(full_prompt, genre.SD_NEGATIVE, seed)
    workflow["9"]["inputs"]["filename_prefix"] = f"{genre.NAME}_shorts"
    client_id = str(uuid.uuid4())

    prompt_id = _comfy_queue_prompt(workflow, client_id)
    history = _comfy_wait(prompt_id)
    outputs = history.get("outputs", {})
    images = outputs.get("9", {}).get("images", [])
    if not images:
        raise RuntimeError(f"No image produced for prompt_id={prompt_id}")
    _comfy_download_image(images[0], out_path)
    return out_path


def comfyui_alive() -> bool:
    try:
        r = requests.get(f"{config.COMFYUI_HOST}/system_stats", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


# ============================================================
# FLUX (Replicate) バックエンド
# ============================================================

def _generate_image_flux(prompt: str, out_path: Path, genre,
                          seed: int | None = None) -> Path:
    """FLUX 1.1 Pro Ultra（Replicate経由）で1枚生成。429は自動リトライ。"""
    import replicate
    from replicate.exceptions import ReplicateError

    token = os.environ.get("REPLICATE_API_TOKEN")
    if not token:
        raise RuntimeError("REPLICATE_API_TOKEN not set in .env")

    full_prompt = genre.SD_STYLE_PREFIX + prompt + genre.SD_STYLE_SUFFIX
    inputs = {
        "prompt": full_prompt,
        "aspect_ratio": config.FLUX_ASPECT_RATIO,
        "output_format": config.FLUX_OUTPUT_FORMAT,
        "raw": config.FLUX_RAW_MODE,
        "safety_tolerance": config.FLUX_SAFETY_TOLERANCE,
    }
    if seed is not None:
        inputs["seed"] = seed

    # 429 (rate limit) / 5xx / NSFW 誤検出 → リトライ
    from replicate.exceptions import ModelError
    output = None
    for attempt in range(8):
        try:
            output = replicate.run(config.FLUX_MODEL, input=inputs)
            break
        except ReplicateError as e:
            msg = str(e)
            if "429" in msg or "throttled" in msg.lower():
                wait = min(30, 10 * (attempt + 1))
                print(f"    rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue
            if "502" in msg or "503" in msg or "504" in msg:
                wait = min(30, 5 * (attempt + 1))
                print(f"    upstream error, retrying in {wait}s...")
                time.sleep(wait)
                continue
            raise
        except ModelError as e:
            msg = str(e)
            if "NSFW" in msg.upper():
                # シードを変えて再試行
                inputs["seed"] = (inputs.get("seed", 0) + 17) % (2**32) or 1
                print(f"    NSFW false-positive, retrying with new seed...")
                continue
            raise
    if output is None:
        raise RuntimeError("FLUX generation failed after retries")

    # outputは FileOutput object もしくは URL string（version次第）
    if hasattr(output, "read"):
        # FileOutput object
        data = output.read()
    elif isinstance(output, (list, tuple)):
        # 古いバージョンはリストを返すことがある
        first = output[0]
        if hasattr(first, "read"):
            data = first.read()
        else:
            data = requests.get(str(first), timeout=60).content
    else:
        # URL string
        data = requests.get(str(output), timeout=60).content

    out_path.write_bytes(data)
    return out_path


def flux_alive() -> bool:
    """REPLICATE_API_TOKEN が設定されているかだけチェック（実通信はしない）"""
    return bool(os.environ.get("REPLICATE_API_TOKEN"))


# ============================================================
# Public API
# ============================================================

def generate_image(prompt: str, out_path: Path, genre,
                    seed: int | None = None) -> Path:
    """config.IMAGE_BACKEND に応じて適切なバックエンドで1枚生成"""
    backend = config.IMAGE_BACKEND
    if backend == "comfyui":
        return _generate_image_comfyui(prompt, out_path, genre, seed)
    elif backend == "flux_replicate":
        return _generate_image_flux(prompt, out_path, genre, seed)
    else:
        raise ValueError(f"Unknown IMAGE_BACKEND: {backend}")


def backend_alive() -> tuple[bool, str]:
    """選択中のバックエンドが利用可能か。(ok, error_message)"""
    backend = config.IMAGE_BACKEND
    if backend == "comfyui":
        if comfyui_alive():
            return True, ""
        return False, f"ComfyUI が起動していません ({config.COMFYUI_HOST})"
    elif backend == "flux_replicate":
        if flux_alive():
            return True, ""
        return False, "REPLICATE_API_TOKEN が .env に設定されていません"
    return False, f"Unknown IMAGE_BACKEND: {backend}"


def _get_or_fetch_scene_image(scene: dict, out_path: Path, genre) -> tuple[Path, dict | None]:
    """1シーン分の画像を入手。返り値: (image_path, attribution_dict_or_None)
    優先順位: entity local → Unsplash → Pexels → FLUX生成"""
    # 1) entity ローカル
    entity_path = config.find_entity_image(scene.get("entity"))
    if entity_path is not None:
        print(f"    [entity] using {entity_path.name}")
        return entity_path, None

    # 2) Web検索 (Unsplash → Pexels)
    keyword = scene.get("image_search_keyword") or ""
    if keyword.strip():
        attribution = web_image_search.search_and_download(keyword, out_path)
        if attribution is not None:
            return out_path, attribution

    # 3) FLUX/ComfyUI 生成
    prompt = scene.get("image_prompt", "abstract scene")
    print(f"    [generate] {prompt[:60]}...")
    generate_image(prompt, out_path, genre)
    return out_path, None


def generate_all(script: dict, run_dir: Path, genre) -> dict:
    """script内の全シーンの画像を入手（キャッシュ + Web優先 + 生成フォールバック）"""
    img_dir = run_dir / "images"
    img_dir.mkdir(parents=True, exist_ok=True)

    attributions: list[dict] = []
    result = {}
    for scene in script["scenes"]:
        sid = scene["scene_id"]
        # キャッシュ確認（拡張子は問わない）
        cached = None
        for ext in ("png", "jpg", "jpeg", "webp"):
            p = img_dir / f"scene_{sid:02d}.{ext}"
            if p.exists() and p.stat().st_size > 0:
                cached = p
                break
        if cached:
            print(f"  [image] scene {sid}: cached ({cached.suffix})")
            result[sid] = cached
            # キャッシュ済みの attribution は scene 側に保存されているはず
            attr = scene.get("_attribution")
            if attr:
                attributions.append(attr)
            continue

        path = img_dir / f"scene_{sid:02d}.jpg"
        print(f"  [image] scene {sid}:")
        img_path, attribution = _get_or_fetch_scene_image(scene, path, genre)
        result[sid] = img_path
        if attribution:
            scene["_attribution"] = attribution
            attributions.append(attribution)

    # script に集約された attributions を保存（後続でYouTube概要欄を組み立てるため）
    script["_attributions"] = attributions
    return result


if __name__ == "__main__":
    import sys
    from genres import load_genre
    ok, err = backend_alive()
    if not ok:
        print(f"❌ {err}")
        raise SystemExit(1)
    g = load_genre(sys.argv[1] if len(sys.argv) > 1 else "ai_news")
    out = Path("test_image.jpg")
    generate_image(
        "executives in suits shaking hands at modern conference room, professional press photo",
        out,
        g,
    )
    print(f"Generated {out} [backend={config.IMAGE_BACKEND}, genre={g.NAME}]")
