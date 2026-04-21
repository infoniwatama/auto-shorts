"""チャンネルブランディング用画像を FLUX で生成（単発スクリプト）"""
import os
import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).parent.parent))
import config  # noqa
import replicate  # noqa
from dotenv import load_dotenv
import requests

load_dotenv(Path(__file__).parent.parent / ".env")

OUT = Path(__file__).parent.parent / "assets" / "channel"
OUT.mkdir(parents=True, exist_ok=True)


def gen(prompt: str, out_name: str, aspect_ratio: str = "1:1") -> Path:
    import time
    from replicate.exceptions import ReplicateError, ModelError
    print(f"🎨 {out_name}...")
    inputs = {
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "output_format": "jpg",
        "raw": False,
        "safety_tolerance": 6,
    }
    for attempt in range(10):
        try:
            output = replicate.run("black-forest-labs/flux-1.1-pro-ultra", input=inputs)
            break
        except ReplicateError as e:
            msg = str(e)
            if "429" in msg or "throttled" in msg.lower():
                wait = min(30, 12 * (attempt + 1))
                print(f"   rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue
            raise
        except ModelError as e:
            if "NSFW" in str(e).upper():
                print("   NSFW false-positive, retrying...")
                continue
            raise
    else:
        raise RuntimeError("FLUX failed after retries")
    if hasattr(output, "read"):
        data = output.read()
    else:
        data = requests.get(str(output), timeout=60).content
    p = OUT / out_name
    p.write_bytes(data)
    print(f"   → {p}")
    return p


ICON_PROMPTS = {
    "icon_v1_chip.jpg":
        "minimalist logo design, stylized AI microchip silhouette viewed from "
        "above, glowing red accent in the center, clean geometric shape, "
        "professional broadcast news brand, strong contrast on pure black "
        "background, centered composition, iconic, vector style",

    "icon_v2_network.jpg":
        "minimalist logo, abstract AI neural network with a single bright red "
        "glowing node at center connected by thin white lines to smaller white "
        "dots, clean and modern, professional news channel brand, pure black "
        "background, centered, simple, iconic",

    "icon_v3_ai_letters.jpg":
        "bold modern logo with the letters 'AI' in sans-serif geometric font, "
        "white letters with red horizontal accent bar underneath, "
        "professional broadcast news style, pure black background, centered, "
        "strong contrast, simple flat design, iconic square composition",

    "icon_v4_breaking_banner.jpg":
        "breaking news banner style logo, bold bright red rectangular badge "
        "with sharp corners filling most of the frame, white bold sans-serif "
        "letters 'AI' in the center of the red banner, modern TV news "
        "broadcast graphic, professional, iconic square composition, "
        "minimalist flat design, centered, high contrast",

    "icon_v5_tv_screen.jpg":
        "retro television silhouette icon with a bright red screen showing a "
        "white glowing neural network node symbol, classic broadcast news TV "
        "set shape, clean flat vector style, centered on pure black "
        "background, professional iconic logo, simple bold composition",

    "icon_v6_live_mic.jpg":
        "news reporter microphone silhouette in white with a red 'LIVE' "
        "rectangular badge attached to the mic head showing white bold letters "
        "'AI', professional broadcast news logo, clean iconic vector style, "
        "centered composition, pure black background, flat design",
}


BANNER_PROMPTS = {
    "banner_v1_newsroom.jpg":
        "wide panoramic news studio set with large dark blue screens in the "
        "background, red accent lighting, horizontal composition wider than "
        "tall, dramatic professional broadcast news atmosphere, cinematic, "
        "high detail, no people, no text",
}


if __name__ == "__main__":
    kind = sys.argv[1] if len(sys.argv) > 1 else "icon"
    # 特定のキーだけ生成（sys.argv[2:] に名前を指定可能）
    keys_filter = set(sys.argv[2:]) if len(sys.argv) > 2 else None

    if kind == "icon":
        for name, prompt in ICON_PROMPTS.items():
            if keys_filter and name not in keys_filter:
                continue
            gen(prompt, name, aspect_ratio="1:1")
    elif kind == "banner":
        for name, prompt in BANNER_PROMPTS.items():
            if keys_filter and name not in keys_filter:
                continue
            gen(prompt, name, aspect_ratio="16:9")
    print("Done")
