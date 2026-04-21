"""Unsplash / Pexels から著作権セーフな画像を検索＆DL。

各検索結果に attribution dict を返し、後続でYouTube概要欄テンプレに使う。
"""
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

import config

load_dotenv(config.ROOT / ".env")


# ============================================================
# Unsplash
# ============================================================

def unsplash_search(keyword: str, orientation: str = "portrait") -> dict | None:
    """Unsplash で1枚検索。結果あれば {url, photographer, photographer_url, source_url, photo_id} を返す"""
    key = os.environ.get("UNSPLASH_ACCESS_KEY")
    if not key:
        return None
    try:
        r = requests.get(
            "https://api.unsplash.com/search/photos",
            params={
                "query": keyword,
                "per_page": 5,
                "orientation": orientation,
                "content_filter": "high",
            },
            headers={"Authorization": f"Client-ID {key}"},
            timeout=15,
        )
        if r.status_code != 200:
            return None
        data = r.json()
        if not data.get("results"):
            return None
        # 1番目を採用（後で複数候補から選ぶ拡張可能）
        photo = data["results"][0]
        return {
            "source": "unsplash",
            "url": photo["urls"]["regular"],   # ~1080px幅
            "download_endpoint": photo["links"]["download_location"],
            "photographer": photo["user"]["name"],
            "photographer_url": photo["user"]["links"]["html"] + "?utm_source=auto-shorts&utm_medium=referral",
            "source_url": photo["links"]["html"] + "?utm_source=auto-shorts&utm_medium=referral",
            "photo_id": photo["id"],
        }
    except Exception as e:
        print(f"  [unsplash] search error: {e}")
        return None


def unsplash_trigger_download(download_endpoint: str) -> None:
    """Unsplash API Guidelines: 画像DL前に必ずこのエンドポイントを叩く（DLカウント用）"""
    key = os.environ.get("UNSPLASH_ACCESS_KEY")
    if not key:
        return
    try:
        requests.get(
            download_endpoint,
            headers={"Authorization": f"Client-ID {key}"},
            timeout=10,
        )
    except Exception:
        pass


# ============================================================
# Pexels
# ============================================================

def pexels_search(keyword: str, orientation: str = "portrait") -> dict | None:
    """Pexels で1枚検索"""
    key = os.environ.get("PEXELS_API_KEY")
    if not key:
        return None
    try:
        r = requests.get(
            "https://api.pexels.com/v1/search",
            params={
                "query": keyword,
                "per_page": 5,
                "orientation": orientation,
            },
            headers={"Authorization": key},
            timeout=15,
        )
        if r.status_code != 200:
            return None
        data = r.json()
        photos = data.get("photos", [])
        if not photos:
            return None
        photo = photos[0]
        return {
            "source": "pexels",
            "url": photo["src"]["large"],   # ~940x1500
            "download_endpoint": None,
            "photographer": photo["photographer"],
            "photographer_url": photo["photographer_url"],
            "source_url": photo["url"],
            "photo_id": str(photo["id"]),
        }
    except Exception as e:
        print(f"  [pexels] search error: {e}")
        return None


# ============================================================
# Public API
# ============================================================

def search_and_download(keyword: str, out_path: Path,
                        prefer_orientation: str = "portrait") -> dict | None:
    """Unsplash → Pexels の順で検索、最初にヒットした画像をDL。
    返り値: attribution dict（DL成功時）or None"""
    if not keyword or not keyword.strip():
        return None

    for fn in (unsplash_search, pexels_search):
        info = fn(keyword, orientation=prefer_orientation)
        if info is None:
            continue
        # Unsplash は DL前にtriggerが必要
        if info.get("download_endpoint"):
            unsplash_trigger_download(info["download_endpoint"])
        try:
            img = requests.get(info["url"], timeout=60)
            img.raise_for_status()
            out_path.write_bytes(img.content)
            print(f"  [{info['source']}] '{keyword}' → {info['photographer']}")
            return info
        except Exception as e:
            print(f"  [{info['source']}] download failed: {e}")
            continue
    return None


def build_attribution_block(attributions: list[dict]) -> str:
    """YouTube概要欄に貼るクレジット文を生成"""
    lines = ["", "🖼️ Image Credits:"]
    seen = set()
    for a in attributions:
        if a is None:
            continue
        key = (a.get("source"), a.get("photo_id"))
        if key in seen:
            continue
        seen.add(key)
        if a["source"] == "unsplash":
            lines.append(
                f"  Photo by {a['photographer']} ({a['photographer_url']}) on Unsplash ({a['source_url']})"
            )
        elif a["source"] == "pexels":
            lines.append(
                f"  Photo by {a['photographer']} ({a['photographer_url']}) on Pexels ({a['source_url']})"
            )
    return "\n".join(lines)


if __name__ == "__main__":
    # smoke test
    out = Path("test_unsplash.jpg")
    info = search_and_download("data center server room", out)
    if info:
        print(f"Saved {out} from {info['source']}, photographer: {info['photographer']}")
    else:
        print("No image found")
