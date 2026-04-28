"""Replicate stable-audio-open でニュース系SEを生成"""
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

OUT = Path(__file__).parent.parent / "assets" / "sfx" / "ai_news"
OUT.mkdir(parents=True, exist_ok=True)

# stable-audio-open-1.0 by stackadoc (working as of 2026)
MODEL_ID = "stackadoc/stable-audio-open-1.0:9aff84e0b15ef32606bb3847e1be39a0e22d4ad6e2746b09f9f83b16b0e63a36"

# 各SEは2-3秒。short impactを狙う。
PROMPTS = {
    "se_impact_drum.mp3":
        "single dramatic news impact drum hit, deep boom with reverb, cinematic, 2 seconds, short",
    "se_breaking_alert.mp3":
        "breaking news alert jingle, urgent electronic stinger, 3 seconds short",
    "se_dramatic_riser.mp3":
        "short dramatic riser sound effect rising tension swoop, 2 seconds, cinematic",
    "se_reveal_chime.mp3":
        "magical reveal sparkle chime sound effect, positive notification, 1 second, short",
    "se_camera_shutter.mp3":
        "camera shutter click flash sound effect, fast paparazzi style, 1 second short",
    "se_suspense_drone.mp3":
        "low rumbling suspense drone, ominous tense ambient, 3 seconds short",
    "se_typing_keyboard.mp3":
        "fast typing keyboard sound effect, journalist news writing, 2 seconds",
    "se_swoosh_transition.mp3":
        "fast cinematic swoosh whoosh transition sound effect, 1 second short",
    "se_glitch_news.mp3":
        "short digital glitch transition sound effect modern news, 1 second",
    "se_warning_beep.mp3":
        "urgent warning siren beep alert sound, news emergency, 2 seconds short",
}


def gen(prompt: str, out_name: str, duration: float = 2.0) -> Path:
    print(f"🔊 {out_name}...")
    inputs = {
        "prompt": prompt,
        "seconds_total": duration,
    }
    for attempt in range(5):
        try:
            output = replicate.run(MODEL_ID, input=inputs)
            break
        except Exception as e:
            wait = min(60, 15 * (attempt + 1))
            print(f"   error (retry in {wait}s): {str(e)[:120]}")
            time.sleep(wait)
    else:
        raise RuntimeError("stable-audio failed after retries")

    if hasattr(output, "read"):
        data = output.read()
    else:
        url = str(output)
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
            # 各SEのdurationを名前から推測
            dur = 3.0 if "drone" in name or "alert" in name else 2.0
            gen(prompt, name, dur)
        except Exception as e:
            print(f"   ❌ {name} failed: {e}")
    print("Done")
