from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def plot_equity_curve(trades_df: pd.DataFrame, portfolio_id: int | None = None) -> go.Figure:
    df = trades_df.copy()
    if portfolio_id is not None:
        df = df[df["Port_IDs"] == portfolio_id]

    if df.empty:
        return px.line(title="Equity Curve")

    equity = (
        df.sort_values("time").groupby("time")["realizedProfit"].sum().cumsum().rename("Equity").reset_index()
    )
    fig = px.line(equity, x="time", y="Equity", title="Equity Curve", markers=True)
    fig.update_layout(xaxis_title="Time", yaxis_title="Cumulative PnL")
    return fig


def plot_drawdown_curve(trades_df: pd.DataFrame, portfolio_id: int | None = None) -> go.Figure:
    df = trades_df.copy()
    if portfolio_id is not None:
        df = df[df["Port_IDs"] == portfolio_id]

    if df.empty:
        return px.area(title="Drawdown Curve")

    equity = df.sort_values("time")["realizedProfit"].cumsum()
    drawdown = equity - equity.cummax()
    drawdown_df = pd.DataFrame({"time": df.sort_values("time")["time"].values, "Drawdown": drawdown.values})
    fig = px.area(drawdown_df, x="time", y="Drawdown", title="Drawdown Curve", color_discrete_sequence=["#d62728"])
    fig.update_layout(xaxis_title="Time", yaxis_title="Drawdown (USDT)")
    return fig


def plot_profit_distribution(trades_df: pd.DataFrame) -> go.Figure:
    fig = px.histogram(
        trades_df,
        x="realizedProfit",
        nbins=50,
        title="Profit Distribution",
        marginal="box",
        color_discrete_sequence=["#1f77b4"],
    )
    fig.update_layout(xaxis_title="Realized Profit", yaxis_title="Trades")
    return fig


def plot_profitability_heatmap(trades_df: pd.DataFrame) -> go.Figure:
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
        title="Hourly Profitability Heatmap",
        color_continuous_scale="Viridis",
    )
    fig.update_layout(xaxis_title="Hour of Day", yaxis_title="Weekday")
    return fig
