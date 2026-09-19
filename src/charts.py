"""Plotly chart builders using the fixed-order categorical palette."""
import plotly.graph_objects as go

# Fixed-order categorical palette (validated for colorblind-safety); never cycle
# by rank - each asset class keeps the same color everywhere it appears.
CATEGORICAL_PALETTE = [
    "#2a78d6",  # blue
    "#eb6834",  # orange
    "#1baf7a",  # aqua
    "#eda100",  # yellow
    "#e87ba4",  # magenta
    "#008300",  # green
    "#4a3aa7",  # violet
    "#e34948",  # red
]

INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRIDLINE = "#e1e0d9"
BASELINE = "#c3c2b7"
SURFACE = "#fcfcfb"


def color_map(asset_classes: list[str]) -> dict[str, str]:
    """Assign palette colors in a fixed order based on the class list order."""
    return {
        name: CATEGORICAL_PALETTE[i % len(CATEGORICAL_PALETTE)]
        for i, name in enumerate(asset_classes)
    }


def _apply_layout(fig: go.Figure, title: str | None = None) -> go.Figure:
    fig.update_layout(
        title=title,
        plot_bgcolor=SURFACE,
        paper_bgcolor=SURFACE,
        font=dict(color=INK_PRIMARY, family="system-ui, -apple-system, 'Segoe UI', sans-serif"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=10, r=10, t=60 if title else 20, b=10),
        hovermode="x unified",
    )
    fig.update_xaxes(gridcolor=GRIDLINE, linecolor=BASELINE, tickfont=dict(color=INK_MUTED))
    fig.update_yaxes(gridcolor=GRIDLINE, linecolor=BASELINE, tickfont=dict(color=INK_MUTED))
    return fig


def stacked_area_with_total(wide_df, classes: list[str]) -> go.Figure:
    """Stacked area of asset-class balances over time, with a total overlay line."""
    cmap = color_map(classes)
    fig = go.Figure()
    for name in classes:
        if name not in wide_df.columns:
            continue
        fig.add_trace(
            go.Scatter(
                x=wide_df.index,
                y=wide_df[name],
                name=name,
                mode="lines",
                stackgroup="assets",
                line=dict(width=2, color=cmap[name]),
                fillcolor=cmap[name],
                hovertemplate="%{y:,.0f} 円<extra>" + name + "</extra>",
            )
        )
    total = wide_df.sum(axis=1)
    fig.add_trace(
        go.Scatter(
            x=wide_df.index,
            y=total,
            name="合計",
            mode="lines+markers",
            line=dict(width=2, color=INK_PRIMARY, dash="dot"),
            marker=dict(size=6, color=INK_PRIMARY),
            hovertemplate="合計 %{y:,.0f} 円<extra></extra>",
        )
    )
    _apply_layout(fig, "資産クラス別 残高推移")
    fig.update_yaxes(tickformat=",")
    return fig


def allocation_donut(latest_row, classes: list[str]) -> go.Figure:
    """Donut chart of the latest month's allocation across asset classes."""
    cmap = color_map(classes)
    labels = [c for c in classes if c in latest_row.index and latest_row[c] > 0]
    values = [latest_row[c] for c in labels]
    colors = [cmap[c] for c in labels]
    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.55,
                marker=dict(colors=colors, line=dict(color=SURFACE, width=2)),
                textinfo="label+percent",
                hovertemplate="%{label}: %{value:,.0f} 円 (%{percent})<extra></extra>",
            )
        ]
    )
    _apply_layout(fig, "最新月のポートフォリオ配分")
    fig.update_layout(legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.05))
    return fig


def total_trend_line(wide_df) -> go.Figure:
    """Simple total-assets trend line."""
    total = wide_df.sum(axis=1)
    fig = go.Figure(
        data=[
            go.Scatter(
                x=wide_df.index,
                y=total,
                mode="lines+markers",
                line=dict(width=2, color=CATEGORICAL_PALETTE[0]),
                marker=dict(size=6, color=CATEGORICAL_PALETTE[0]),
                hovertemplate="%{y:,.0f} 円<extra></extra>",
            )
        ]
    )
    _apply_layout(fig, "総資産推移")
    fig.update_yaxes(tickformat=",")
    return fig
