"""ジャンルプロファイル動的ローダー"""
import importlib


def load_genre(name: str):
    """ジャンル名からモジュールを動的ロード（例: 'horror' → genres.horror）"""
    return importlib.import_module(f"genres.{name}")


def list_genres():
    import pkgutil
    return [m.name for m in pkgutil.iter_modules(__path__) if not m.name.startswith("_")]
