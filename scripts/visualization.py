from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def plot_equity_curve(trades_df: pd.DataFrame, portfolio_id: int | None = None) -> go.Figure:
    """Plot cumulative equity curve from trades with smoothing for high-density data."""
    df = trades_df.copy()
    if portfolio_id is not None:
        df = df[df["Port_IDs"] == portfolio_id]

    if df.empty:
        return px.line(title="Equity Curve - No Data")

    df = df.sort_values("time")
    
    # If too many points, aggregate to hourly to reduce noise
    if len(df) > 500:
        df["time"] = df["time"].dt.floor("H")
        equity = df.groupby("time")["realizedProfit"].sum().cumsum().rename("Equity").reset_index()
    else:
        equity = df.groupby("time")["realizedProfit"].sum().cumsum().rename("Equity").reset_index()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=equity["time"],
        y=equity["Equity"],
        mode="lines",
        name="Equity",
        line=dict(color="#0066cc", width=2.5),
        fill='tozeroy',
        fillcolor='rgba(0, 102, 204, 0.1)',
        hovertemplate="<b>Date:</b> %{x}<br><b>PnL:</b> %{y:,.2f} USDT<extra></extra>"
    ))
    
    fig.update_layout(
        title="Cumulative Equity Performance (Realized PnL)",
        hovermode="x unified",
        template="plotly_white",
        height=500,
        xaxis=dict(title="Timeline", showgrid=True, gridcolor='rgba(0,0,0,0.05)'),
        yaxis=dict(title="Cumulative PnL (USDT)", showgrid=True, gridcolor='rgba(0,0,0,0.05)', tickformat=",.0f"),
        margin=dict(l=20, r=20, t=50, b=20),
    )
    
    return fig


def plot_drawdown_curve(trades_df: pd.DataFrame, portfolio_id: int | None = None) -> go.Figure:
    """Plot drawdown curve with noise reduction for high-density data."""
    df = trades_df.copy()
    if portfolio_id is not None:
        df = df[df["Port_IDs"] == portfolio_id]

    if df.empty:
        return px.area(title="Drawdown Curve - No Data")

    df = df.sort_values("time")
    
    # Pre-calculate equity to identify drawdown
    df["cum_pnl"] = df["realizedProfit"].cumsum()
    df["drawdown"] = df["cum_pnl"] - df["cum_pnl"].cummax()
    
    # If too many points, aggregate to hourly
    if len(df) > 500:
        df["time"] = df["time"].dt.floor("H")
        drawdown_df = df.groupby("time")["drawdown"].min().rename("Drawdown").reset_index()
    else:
        drawdown_df = df[["time", "drawdown"]].rename(columns={"drawdown": "Drawdown"})
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=drawdown_df["time"],
        y=drawdown_df["Drawdown"],
        mode="lines",
        name="Drawdown",
        fill='tozeroy',
        line=dict(color="#e44c4c", width=1.5),
        fillcolor='rgba(228, 76, 76, 0.2)',
        hovertemplate="<b>Date:</b> %{x}<br><b>Drawdown:</b> %{y:,.2f} USDT<extra></extra>"
    ))
    
    fig.update_layout(
        title="Peak-to-Trough Drawdown Analysis",
        hovermode="x unified",
        template="plotly_white",
        height=400,
        xaxis=dict(title="Timeline", showgrid=True, gridcolor='rgba(0,0,0,0.05)'),
        yaxis=dict(title="Drawdown (USDT)", showgrid=True, gridcolor='rgba(0,0,0,0.05)', tickformat=",.0f"),
        margin=dict(l=20, r=20, t=50, b=20),
    )
    
    return fig


def plot_profit_distribution(trades_df: pd.DataFrame) -> go.Figure:
    """Plot histogram of profit distribution with statistics.
    
    Args:
        trades_df: DataFrame with trade data
        
    Returns:
        Plotly figure with profit distribution
    """
    fig = px.histogram(
        trades_df,
        x="realizedProfit",
        nbins=50,
        title="Trade Profit Distribution (with Box Plot)",
        marginal="box",
        labels={"realizedProfit": "Realized Profit (USDT)", "count": "Number of Trades"},
        color_discrete_sequence=["#1f77b4"],
    )
    
    fig.update_layout(
        hovermode="x unified",
        template="plotly_white",
        height=450,
        xaxis_title="Realized Profit (USDT)",
        yaxis_title="Trade Count",
        showlegend=True,
        legend=dict(x=0.01, y=0.99),
    )
    
    # Add mean and median lines
    mean_profit = trades_df["realizedProfit"].mean()
    median_profit = trades_df["realizedProfit"].median()
    
    fig.add_vline(
        x=mean_profit,
        line_dash="dash",
        line_color="green",
        annotation_text=f"Mean: {mean_profit:.2f}",
        annotation_position="top right",
        name="Mean"
    )
    
    fig.add_vline(
        x=median_profit,
        line_dash="dot",
        line_color="orange",
        annotation_text=f"Median: {median_profit:.2f}",
        annotation_position="top left",
        name="Median"
    )
    
    return fig


def plot_profitability_heatmap(trades_df: pd.DataFrame) -> go.Figure:
    """Plot profitability heatmap by weekday and hour of day.
    
    Args:
        trades_df: DataFrame with trade data
        
    Returns:
        Plotly heatmap figure
    """
    df = trades_df.copy()
    df["weekday"] = pd.Categorical(
        df["time"].dt.day_name(),
        categories=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        ordered=True,
    )
    df["hour"] = df["time"].dt.hour
    
    heatmap_data = (
        df.groupby(["weekday", "hour"])["realizedProfit"]
        .sum()
        .reset_index()
    )
    
    fig = px.density_heatmap(
        heatmap_data,
        x="hour",
        y="weekday",
        z="realizedProfit",
        title="Hourly Profitability Heatmap by Weekday",
        labels={
            "hour": "Hour of Day (UTC)",
            "weekday": "Day of Week",
            "realizedProfit": "Total PnL (USDT)"
        },
        color_continuous_scale="Viridis",
        nbinsx=24,
        nbinsy=7,
    )
    
    fig.update_layout(
        hovermode="closest",
        template="plotly_white",
        height=450,
        xaxis_title="Hour of Day (UTC)",
        yaxis_title="Day of Week",
        coloraxis_colorbar=dict(
            title="PnL (USDT)",
            thickness=15,
            len=0.7
        ),
    )
    
    fig.update_xaxes(
        tickmode="linear",
        tick0=0,
        dtick=1,
    )
    
    return fig
