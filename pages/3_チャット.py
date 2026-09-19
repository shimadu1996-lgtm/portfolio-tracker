import streamlit as st

from src import data_store, gemini_client, ui_common

st.set_page_config(page_title="チャット", page_icon="💬", layout="wide")
ui_common.render_sidebar_status()
st.title("💬 資産データについてAIに質問する")

df = data_store.load_portfolio()
if df.empty:
    st.info("まだデータがありません。先に「データ入力」で登録してください。")
    st.stop()

wide = data_store.pivot_wide(df)
notes = data_store.load_notes()

if "chat_messages" not in st.session_state:
    st.session_state["chat_messages"] = []

if st.button("🗑️ 会話をクリア"):
    st.session_state["chat_messages"] = []
    st.rerun()

for m in st.session_state["chat_messages"]:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

user_msg = st.chat_input("例: 先月と比べて配分はどう変わった?")
if user_msg:
    st.session_state["chat_messages"].append({"role": "user", "content": user_msg})
    with st.chat_message("user"):
        st.markdown(user_msg)

    with st.chat_message("assistant"):
        with st.spinner("考え中..."):
            try:
                reply = gemini_client.chat_reply(st.session_state["chat_messages"], wide, notes)
            except RuntimeError as e:
                reply = f"エラー: {e}"
        st.markdown(reply)
    st.session_state["chat_messages"].append({"role": "assistant", "content": reply})
