from datetime import date

import pandas as pd
import streamlit as st

from src import config, data_store, gemini_client, ui_common

st.set_page_config(page_title="データ入力", page_icon="📝", layout="wide")
ui_common.render_sidebar_status()
st.title("📝 月次データ入力")

classes = config.get_asset_classes()

today = date.today()
sel_date = st.date_input("対象月", value=date(today.year, today.month, 1))
target_month = date(sel_date.year, sel_date.month, 1)
month_key = target_month.strftime("%Y-%m-%d")

if st.session_state.get("loaded_month") != month_key:
    existing = data_store.get_month_allocations(target_month)
    for c in classes:
        st.session_state[f"alloc_{c}"] = float(existing.get(c, 0.0))
    st.session_state["loaded_month"] = month_key
    st.session_state["current_memo"] = data_store.load_notes().get(month_key, "")

st.divider()

with st.expander("📷 スクリーンショット/PDFから自動入力(Gemini)"):
    uploaded = st.file_uploader(
        "証券会社・銀行の残高画面など", type=["png", "jpg", "jpeg", "webp", "pdf"]
    )
    if uploaded is not None and st.button("AIで読み取る"):
        with st.spinner("Geminiが読み取り中..."):
            try:
                extracted = gemini_client.extract_allocations_from_file(
                    uploaded.getvalue(), uploaded.type, classes
                )
            except RuntimeError as e:
                st.error(str(e))
                extracted = {}
        if extracted:
            for name, amount in extracted.items():
                if name not in classes:
                    classes = config.add_asset_class(name)
                st.session_state[f"alloc_{name}"] = amount
            st.success(f"{len(extracted)}件の項目を読み取りました。内容を確認のうえ保存してください。")
            st.rerun()
        else:
            st.warning("読み取れる金額が見つかりませんでした。")

st.divider()

st.subheader("資産クラス別残高(円)")
cols = st.columns(2)
for i, c in enumerate(classes):
    with cols[i % 2]:
        st.number_input(
            c,
            min_value=0.0,
            step=1000.0,
            value=st.session_state.get(f"alloc_{c}", 0.0),
            key=f"alloc_{c}",
            format="%.0f",
        )

with st.form("add_class_form", clear_on_submit=True):
    new_class = st.text_input("新しい資産クラスを追加")
    if st.form_submit_button("追加") and new_class.strip():
        config.add_asset_class(new_class)
        st.rerun()

memo = st.text_area("この月のメモ(任意)", key="current_memo")

total_input = sum(st.session_state.get(f"alloc_{c}", 0.0) for c in classes)
st.metric("入力合計", f"¥{total_input:,.0f}")

if st.button("💾 この月のデータを保存", type="primary"):
    allocations = {c: st.session_state.get(f"alloc_{c}", 0.0) for c in classes}
    data_store.upsert_month(target_month, allocations)
    data_store.save_note(target_month, memo)
    st.success(f"{target_month:%Y年%m月}のデータを保存しました。")

st.divider()
st.subheader("履歴の編集")
df = data_store.load_portfolio()
if not df.empty:
    wide = data_store.pivot_wide(df)
    edit_df = wide.copy()
    edit_df.index = edit_df.index.strftime("%Y-%m-%d")
    edit_df = edit_df.reset_index().rename(columns={"index": "date"})
    edited = st.data_editor(edit_df, num_rows="dynamic", use_container_width=True, key="history_editor")
    if st.button("履歴の変更を保存"):
        long_rows = []
        for _, row in edited.iterrows():
            if not row.get("date"):
                continue
            for c in edit_df.columns:
                if c == "date":
                    continue
                amt = row[c]
                if pd.notna(amt) and amt:
                    long_rows.append({"date": row["date"], "asset_class": c, "amount": float(amt)})
        new_long = pd.DataFrame(long_rows, columns=data_store.COLUMNS)
        data_store.replace_all(new_long)
        st.success("履歴を更新しました。")
        st.rerun()
else:
    st.caption("まだ履歴はありません。")
