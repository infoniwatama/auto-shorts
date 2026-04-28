"""Replicate MusicGen でニュースShort用BGMを生成"""
import os
import sys
import time
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).parent.parent))
import replicate
from dotenv import load_dotenv
import requests

load_dotenv(Path(__file__).parent.parent / ".env")

OUT = Path(__file__).parent.parent / "assets" / "bgm" / "ai_news"
OUT.mkdir(parents=True, exist_ok=True)

PROMPTS = {
    "musicgen_tense_breaking.mp3":
        "tense breaking news intro music, urgent driving electronic beat, "
        "cinematic synth pulses, modern broadcast underscore, no vocals, "
        "instrumental, 90bpm, dark and serious mood",

    "musicgen_modern_underscore.mp3":
        "modern news broadcast underscore, dark electronic ambient, "
        "subtle suspense, low frequency pulses, instrumental no vocals, "
        "minimalist tension, professional documentary style, 80bpm",

    "musicgen_investigative.mp3":
        "investigative journalism background score, slow tension build, "
        "electronic strings, cinematic undertone, mysterious, no vocals, "
        "instrumental, 70bpm, sophisticated brooding atmosphere",

    "musicgen_breaking_drums.mp3":
        "dramatic news headline music, fast paced cinematic drums, "
        "modern hip-hop trap beat, urgent breaking news vibe, intense, "
        "no vocals, instrumental, 100bpm, punchy and energetic",
}


def gen(prompt: str, out_name: str, duration: int = 30) -> Path:
    print(f"🎵 {out_name}...")
    print(f"   prompt: {prompt[:80]}...")
    inputs = {
        "prompt": prompt,
        "duration": duration,
        "model_version": "large",
        "output_format": "mp3",
        "normalization_strategy": "loudness",
    }
    # 2025/2026時点で動くMusicGenのバージョン固定ハッシュ
    model_id = "meta/musicgen:7a76a8258b23fae65c5a22debb8841d1d7e816b75c2f24218cd2bd8573787906"
    for attempt in range(5):
        try:
            output = replicate.run(model_id, input=inputs)
            break
        except Exception as e:
            wait = min(60, 15 * (attempt + 1))
            print(f"   error (retry in {wait}s): {e}")
            time.sleep(wait)
    else:
        raise RuntimeError("MusicGen failed after retries")

    if hasattr(output, "read"):
        data = output.read()
    else:
        url = str(output)
        print(f"   downloading: {url[:60]}...")
        data = requests.get(url, timeout=120).content

    p = OUT / out_name
    p.write_bytes(data)
    print(f"   → {p} ({len(data) // 1024} KB)")
    return p


if __name__ == "__main__":
    keys_filter = set(sys.argv[1:]) if len(sys.argv) > 1 else None
    for name, prompt in PROMPTS.items():
        if keys_filter and name not in keys_filter:
            continue
        try:
            gen(prompt, name)
        except Exception as e:
            print(f"   ❌ {name} failed: {e}")
    print("Done")
