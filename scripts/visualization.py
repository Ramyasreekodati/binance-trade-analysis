from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def plot_equity_curve(trades_df: pd.DataFrame, portfolio_id: int | None = None) -> go.Figure:
    """Plot cumulative equity curve from trades.
    
    Args:
        trades_df: DataFrame with trade data
        portfolio_id: Optional portfolio ID to filter
        
    Returns:
        Plotly figure with equity curve
    """
    df = trades_df.copy()
    if portfolio_id is not None:
        df = df[df["Port_IDs"] == portfolio_id]

    if df.empty:
        return px.line(title="Equity Curve - No Data")

    equity = (
        df.sort_values("time").groupby("time")["realizedProfit"].sum().cumsum().rename("Equity").reset_index()
    )
    
    fig = px.line(
        equity,
        x="time",
        y="Equity",
        title="Cumulative Equity Curve",
        markers=True,
        labels={"time": "Date/Time", "Equity": "Cumulative PnL (USDT)"}
    )
    
    fig.update_layout(
        hovermode="x unified",
        template="plotly_white",
        height=450,
        xaxis_title="Date/Time",
        yaxis_title="Cumulative PnL (USDT)",
        showlegend=True,
        legend=dict(x=0.01, y=0.99),
    )
    
    fig.update_traces(
        name="Equity",
        line=dict(color="#1f77b4", width=2),
        marker=dict(size=4, opacity=0.6)
    )
    
    return fig


def plot_drawdown_curve(trades_df: pd.DataFrame, portfolio_id: int | None = None) -> go.Figure:
    """Plot drawdown (peak-to-trough decline) from trades.
    
    Args:
        trades_df: DataFrame with trade data
        portfolio_id: Optional portfolio ID to filter
        
    Returns:
        Plotly figure with drawdown curve
    """
    df = trades_df.copy()
    if portfolio_id is not None:
        df = df[df["Port_IDs"] == portfolio_id]

    if df.empty:
        return px.area(title="Drawdown Curve - No Data")

    equity = df.sort_values("time")["realizedProfit"].cumsum()
    drawdown = equity - equity.cummax()
    drawdown_df = pd.DataFrame({
        "time": df.sort_values("time")["time"].values,
        "Drawdown": drawdown.values
    })
    
    fig = px.area(
        drawdown_df,
        x="time",
        y="Drawdown",
        title="Drawdown Curve (Peak-to-Trough Decline)",
        labels={"time": "Date/Time", "Drawdown": "Drawdown (USDT)"},
        color_discrete_sequence=["#d62728"]
    )
    
    fig.update_layout(
        hovermode="x unified",
        template="plotly_white",
        height=450,
        xaxis_title="Date/Time",
        yaxis_title="Drawdown (USDT)",
        showlegend=True,
        legend=dict(x=0.01, y=0.99),
    )
    
    fig.update_traces(
        name="Drawdown",
        fillcolor="rgba(214, 39, 40, 0.3)",
        line=dict(color="#d62728", width=2)
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
