from datetime import date, datetime

import streamlit as st

from src import config, data_store, gemini_client, ui_common

st.set_page_config(page_title="AIコメント", page_icon="🤖", layout="wide")
ui_common.render_sidebar_status()
st.title("🤖 AIによる月次コメント")

df = data_store.load_portfolio()
if df.empty:
    st.info("まだデータがありません。先に「データ入力」で登録してください。")
    st.stop()

wide = data_store.pivot_wide(df)
notes = data_store.load_notes()

months = list(wide.index)
default_idx = len(months) - 1
sel = st.selectbox(
    "対象月",
    options=months,
    index=default_idx,
    format_func=lambda d: d.strftime("%Y年%m月"),
)
month_key = sel.strftime("%Y-%m-%d")

if st.button("✨ コメントを生成", type="primary"):
    with st.spinner("Geminiが分析中..."):
        try:
            comment = gemini_client.generate_monthly_comment(wide, notes, month_key)
            data_store.add_comment(
                date(sel.year, sel.month, 1), comment, datetime.now().isoformat(timespec="seconds")
            )
            st.rerun()
        except RuntimeError as e:
            st.error(str(e))

st.divider()
st.subheader(f"{sel:%Y年%m月} のコメント履歴")
comments = data_store.load_comments().get(month_key, [])
if not comments:
    st.caption("まだこの月のコメントはありません。")
else:
    for c in reversed(comments):
        with st.container(border=True):
            st.caption(c["generated_at"])
            st.markdown(c["text"])
