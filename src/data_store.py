"""CSV/JSON-backed persistence for monthly portfolio snapshots (no database)."""
import json
from datetime import date

import pandas as pd

from . import config

COLUMNS = ["date", "asset_class", "amount"]


def load_portfolio() -> pd.DataFrame:
    if not config.PORTFOLIO_CSV.exists():
        return pd.DataFrame(columns=COLUMNS)
    df = pd.read_csv(config.PORTFOLIO_CSV, dtype={"asset_class": str})
    if df.empty:
        return pd.DataFrame(columns=COLUMNS)
    df["date"] = pd.to_datetime(df["date"])
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
    return df


def save_portfolio(df: pd.DataFrame) -> None:
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"]).dt.strftime("%Y-%m-%d")
    out.to_csv(config.PORTFOLIO_CSV, index=False, columns=COLUMNS)


def month_key(d: date) -> pd.Timestamp:
    return pd.Timestamp(year=d.year, month=d.month, day=1)


def get_month_allocations(target_month: date) -> dict[str, float]:
    df = load_portfolio()
    if df.empty:
        return {}
    mk = month_key(target_month)
    rows = df[df["date"] == mk]
    return dict(zip(rows["asset_class"], rows["amount"]))


def upsert_month(target_month: date, allocations: dict[str, float]) -> None:
    """Replace all rows for the given month with the provided allocations."""
    df = load_portfolio()
    mk = month_key(target_month)
    df = df[df["date"] != mk]
    new_rows = pd.DataFrame(
        [{"date": mk, "asset_class": k, "amount": float(v)} for k, v in allocations.items() if v],
        columns=COLUMNS,
    )
    if df.empty:
        df = new_rows
    elif not new_rows.empty:
        df = pd.concat([df, new_rows], ignore_index=True)
    df = df.sort_values(["date", "asset_class"]).reset_index(drop=True)
    save_portfolio(df)


def delete_month(target_month: date) -> None:
    df = load_portfolio()
    mk = month_key(target_month)
    df = df[df["date"] != mk]
    save_portfolio(df)


def pivot_wide(df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Return a date x asset_class table of amounts, sorted by date ascending."""
    if df is None:
        df = load_portfolio()
    if df.empty:
        return pd.DataFrame()
    wide = df.pivot_table(index="date", columns="asset_class", values="amount", aggfunc="sum", fill_value=0.0)
    return wide.sort_index()


def replace_all(long_df: pd.DataFrame) -> None:
    """Overwrite the whole store, used by the history editor."""
    save_portfolio(long_df)


# --- monthly free-text notes ---

def load_notes() -> dict[str, str]:
    if not config.NOTES_JSON.exists():
        return {}
    with open(config.NOTES_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def save_note(target_month: date, text: str) -> None:
    notes = load_notes()
    key = month_key(target_month).strftime("%Y-%m-%d")
    if text.strip():
        notes[key] = text.strip()
    else:
        notes.pop(key, None)
    with open(config.NOTES_JSON, "w", encoding="utf-8") as f:
        json.dump(notes, f, ensure_ascii=False, indent=2)


# --- AI-generated monthly commentary log ---

def load_comments() -> dict[str, list[dict]]:
    if not config.COMMENTS_JSON.exists():
        return {}
    with open(config.COMMENTS_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def add_comment(target_month: date, text: str, generated_at: str) -> None:
    comments = load_comments()
    key = month_key(target_month).strftime("%Y-%m-%d")
    comments.setdefault(key, [])
    comments[key].append({"text": text, "generated_at": generated_at})
    with open(config.COMMENTS_JSON, "w", encoding="utf-8") as f:
        json.dump(comments, f, ensure_ascii=False, indent=2)
