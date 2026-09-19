import streamlit as st

from src import charts, config, data_store, ui_common

st.set_page_config(page_title="資産管理ダッシュボード", page_icon="📊", layout="wide")
ui_common.render_sidebar_status()

st.title("📊 資産管理ダッシュボード")

df = data_store.load_portfolio()

if df.empty:
    st.info("まだデータがありません。左のメニューから「データ入力」で最初の月次残高を登録してください。")
    st.stop()

classes = config.get_asset_classes()
wide = data_store.pivot_wide(df)
# keep only classes that actually appear, preserving the configured fixed order
active_classes = [c for c in classes if c in wide.columns] + [c for c in wide.columns if c not in classes]
total = wide.sum(axis=1)

latest_date = wide.index[-1]
latest_total = total.iloc[-1]

col1, col2, col3 = st.columns(3)
col1.metric("総資産(最新月)", f"¥{latest_total:,.0f}", help=f"{latest_date:%Y年%m月}時点")

if len(total) >= 2:
    prev_total = total.iloc[-2]
    diff = latest_total - prev_total
    pct = (diff / prev_total * 100) if prev_total else 0
    col2.metric("前月比", f"¥{diff:,.0f}", f"{pct:+.1f}%")
else:
    col2.metric("前月比", "―")

year_start = total[total.index.year == latest_date.year]
if len(year_start) >= 2:
    ytd_diff = latest_total - year_start.iloc[0]
    ytd_pct = (ytd_diff / year_start.iloc[0] * 100) if year_start.iloc[0] else 0
    col3.metric("年初来", f"¥{ytd_diff:,.0f}", f"{ytd_pct:+.1f}%")
else:
    col3.metric("年初来", "―")

st.plotly_chart(charts.stacked_area_with_total(wide, active_classes), use_container_width=True)

left, right = st.columns([1, 1])
with left:
    st.plotly_chart(charts.allocation_donut(wide.iloc[-1], active_classes), use_container_width=True)
with right:
    st.subheader("最新月の内訳")
    latest_row = wide.iloc[-1]
    breakdown = latest_row[latest_row > 0].sort_values(ascending=False)
    for name, amount in breakdown.items():
        pct = amount / latest_total * 100 if latest_total else 0
        st.write(f"**{name}**: ¥{amount:,.0f} ({pct:.1f}%)")

with st.expander("履歴データを表示"):
    display = wide.copy()
    display.index = display.index.strftime("%Y-%m")
    display["合計"] = wide.sum(axis=1).values
    st.dataframe(display.style.format("¥{:,.0f}"), use_container_width=True)
