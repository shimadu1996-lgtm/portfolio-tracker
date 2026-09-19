"""Configuration and settings management: asset classes, API key, file paths."""
import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

PORTFOLIO_CSV = DATA_DIR / "portfolio.csv"
NOTES_JSON = DATA_DIR / "notes.json"
COMMENTS_JSON = DATA_DIR / "comments.json"
CONFIG_JSON = DATA_DIR / "config.json"

DEFAULT_ASSET_CLASSES = [
    "国内株式",
    "先進国株式",
    "新興国株式",
    "債券",
    "現金",
    "REIT",
    "暗号資産",
    "その他",
]

GEMINI_MODEL = "gemini-3.6-flash"


def _load_config() -> dict:
    if CONFIG_JSON.exists():
        with open(CONFIG_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_config(cfg: dict) -> None:
    with open(CONFIG_JSON, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def get_asset_classes() -> list[str]:
    cfg = _load_config()
    classes = cfg.get("asset_classes")
    if not classes:
        classes = list(DEFAULT_ASSET_CLASSES)
        cfg["asset_classes"] = classes
        _save_config(cfg)
    return classes


def add_asset_class(name: str) -> list[str]:
    name = name.strip()
    classes = get_asset_classes()
    if name and name not in classes:
        classes.append(name)
        cfg = _load_config()
        cfg["asset_classes"] = classes
        _save_config(cfg)
    return classes


def get_api_key() -> str | None:
    """Look for a Gemini API key: session override, Streamlit secrets, env var."""
    try:
        import streamlit as st

        if st.session_state.get("gemini_api_key_override"):
            return st.session_state["gemini_api_key_override"]
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass
    return os.environ.get("GEMINI_API_KEY")
