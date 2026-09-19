"""Shared sidebar/UI helpers used across all pages."""
import streamlit as st

from . import config


def render_sidebar_status():
    with st.sidebar:
        st.markdown("### Gemini API設定")
        if config.get_api_key():
            st.success("APIキーが設定されています", icon="✅")
            if st.session_state.get("gemini_api_key_override"):
                if st.button("セッションのキーを削除"):
                    del st.session_state["gemini_api_key_override"]
                    st.rerun()
        else:
            key_input = st.text_input(
                "Gemini APIキー",
                type="password",
                help="このセッション中のみメモリに保持され、保存はされません。"
                "secrets.tomlや環境変数で設定すれば毎回入力する必要はありません。",
            )
            if key_input:
                st.session_state["gemini_api_key_override"] = key_input
                st.rerun()
