"""Thin wrapper around the Gemini API: monthly commentary, chat, and
screenshot/PDF data extraction. All calls raise RuntimeError with a Japanese
message on failure so the UI can show st.error(...) directly.
"""
import json
import re

from . import config

_MODEL = config.GEMINI_MODEL


def _client():
    api_key = config.get_api_key()
    if not api_key:
        raise RuntimeError(
            "Gemini APIキーが設定されていません。サイドバーで入力するか、"
            ".streamlit/secrets.toml か環境変数 GEMINI_API_KEY を設定してください。"
        )
    from google import genai

    return genai.Client(api_key=api_key)


def _extract_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    return json.loads(text)


def _format_history_table(wide_df) -> str:
    if wide_df.empty:
        return "(データなし)"
    tail = wide_df.tail(12).copy()
    tail["合計"] = tail.sum(axis=1)
    lines = ["date," + ",".join(list(tail.columns))]
    for idx, row in tail.iterrows():
        lines.append(idx.strftime("%Y-%m") + "," + ",".join(f"{v:,.0f}" for v in row.values))
    return "\n".join(lines)


def generate_monthly_comment(wide_df, notes: dict, target_month_key: str) -> str:
    from google.genai import types

    history_csv = _format_history_table(wide_df)
    note_text = notes.get(target_month_key, "")
    prompt = f"""あなたは個人の資産管理を手伝うアシスタントです。以下は月次の資産クラス別残高の推移(CSV形式、単位は円)です。

{history_csv}

対象月: {target_month_key}
本人のメモ: {note_text or "(なし)"}

このデータをもとに、対象月の資産状況について日本語で簡潔にコメントしてください。
- 全体資産の増減とその傾向
- ポートフォリオ配分のバランス(偏りがあれば指摘)
- 気になる点や次月以降チェックすべきポイント
の3つの観点を、それぞれ1〜2文の箇条書きでまとめてください。
断定的な投資助言は避け、あくまで記録の振り返りとして中立的なトーンで書いてください。
"""
    client = _client()
    try:
        resp = client.models.generate_content(model=_MODEL, contents=prompt)
    except Exception as e:
        raise RuntimeError(f"コメント生成に失敗しました: {e}") from e
    return resp.text


def chat_reply(messages: list[dict], wide_df, notes: dict) -> str:
    """messages: [{"role": "user"|"assistant", "content": str}, ...]"""
    from google.genai import types

    history_csv = _format_history_table(wide_df)
    notes_json = json.dumps(notes, ensure_ascii=False)
    system_instruction = f"""あなたは個人の資産管理を手伝うアシスタントです。ユーザーの月次資産クラス別残高(CSV、単位は円)は以下の通りです。

{history_csv}

月次メモ(日付: メモ): {notes_json}

このデータを踏まえて、ユーザーの質問に日本語で簡潔かつ具体的に答えてください。
数値を挙げる際はデータに基づいて計算し、断定的な投資助言(売買の指示など)は行わず、
中立的な情報提供と気づきの提示にとどめてください。
"""
    contents = []
    for m in messages:
        role = "user" if m["role"] == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part.from_text(text=m["content"])]))

    client = _client()
    try:
        resp = client.models.generate_content(
            model=_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(system_instruction=system_instruction),
        )
    except Exception as e:
        raise RuntimeError(f"チャット応答の取得に失敗しました: {e}") from e
    return resp.text


def extract_allocations_from_file(file_bytes: bytes, mime_type: str, asset_classes: list[str]) -> dict[str, float]:
    """Send a screenshot or PDF of a brokerage statement to Gemini and get back
    a {asset_class: amount} dict. Unknown categories are kept as-is so the UI
    can offer to add them as new asset classes.
    """
    from google.genai import types

    classes_str = "、".join(asset_classes)
    prompt = f"""この画像またはPDFは証券会社・銀行の資産残高画面です。
資産クラスごとの残高(円)を読み取ってください。
既知の資産クラス: {classes_str}
画像内の項目がこれらに対応する場合はその名称を使い、対応しない場合は画像内の表記をそのまま使ってください。
出力は必ず次の形式のJSONのみとしてください(説明文や```は不要):
{{"資産クラス名": 金額の数値, ...}}
金額はカンマや円記号を除いた数値のみにしてください。読み取れない場合はキーを含めないでください。
"""
    part = types.Part.from_bytes(data=file_bytes, mime_type=mime_type)
    client = _client()
    try:
        resp = client.models.generate_content(
            model=_MODEL,
            contents=[part, prompt],
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
    except Exception as e:
        raise RuntimeError(f"データ抽出に失敗しました: {e}") from e

    try:
        data = _extract_json(resp.text)
    except Exception as e:
        raise RuntimeError(f"Geminiの応答をJSONとして解釈できませんでした: {e}\n応答: {resp.text}") from e

    result = {}
    for k, v in data.items():
        try:
            result[str(k)] = float(v)
        except (TypeError, ValueError):
            continue
    return result
