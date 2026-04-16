from __future__ import annotations
import logging
import numpy as np
import pandas as pd
import streamlit as st


def _compute_drawdown(equity_curve: pd.Series) -> pd.Series:
    running_max = equity_curve.cummax()
    return equity_curve - running_max


def _annualized_volatility(returns: pd.Series) -> float:
    if returns.empty:
        return 0.0
    return float(returns.std(ddof=0) * np.sqrt(252))


def portfolio_summary(trades: pd.DataFrame, initial_capital: float = 100000.0) -> pd.Series:
    """Calculate key financial metrics for a portfolio trade series with high robustness."""
    # Ensure initial_capital is a float
    try:
        initial_capital = float(initial_capital)
    except (ValueError, TypeError):
        initial_capital = 100000.0

    if trades.empty:
        return pd.Series({k: 0.0 for k in ["Total_PnL", "Total_Trades", "Win_Rate", "Loss_Rate", "Average_Win", "Average_Loss", "Win_Loss_Ratio", "Trade_Expectancy", "Profit_Factor", "Sharpe_Ratio", "Volatility", "Max_Drawdown", "ROI"]})

    # Validate required columns
    required = ["realizedProfit", "time"]
    for col in required:
        if col not in trades.columns:
            logging.error(f"Missing required column: {col}")
            return pd.Series({k: 0.0 for k in ["Total_PnL", "Total_Trades", "Win_Rate", "Loss_Rate", "Average_Win", "Average_Loss", "Win_Loss_Ratio", "Trade_Expectancy", "Profit_Factor", "Sharpe_Ratio", "Volatility", "Max_Drawdown", "ROI"]})

    trades = trades.sort_values("time")
    
    # Handle NaNs in profit
    profits = trades["realizedProfit"].fillna(0.0)
    
    total_pnl = float(profits.sum())
    total_trades = int(len(trades))
    
    wins = profits[profits > 0]
    losses = profits[profits < 0]
    
    win_rate = float(len(wins) / total_trades * 100) if total_trades > 0 else 0.0
    loss_rate = float(len(losses) / total_trades * 100) if total_trades > 0 else 0.0
    
    average_win = float(wins.mean()) if not wins.empty else 0.0
    average_loss = float(losses.mean()) if not losses.empty else 0.0
    
    expectancy = float(average_win * win_rate / 100 + average_loss * loss_rate / 100)
    win_loss_ratio = float(abs(average_win / average_loss)) if average_loss != 0 else 0.0
    profit_factor = float(wins.sum() / abs(losses.sum())) if losses.sum() != 0 else 0.0

    try:
        daily_returns = trades.set_index("time")["realizedProfit"].fillna(0.0).resample("D").sum()
        annual_volatility = _annualized_volatility(daily_returns)
        std_dev = daily_returns.std(ddof=0)
        sharpe_ratio = float(daily_returns.mean() / std_dev * np.sqrt(252)) if (not daily_returns.empty and std_dev > 0) else 0.0
    except Exception as e:
        logging.warning(f"Portfolio resample error: {e}")
        annual_volatility = 0.0
        sharpe_ratio = 0.0

    equity_curve = profits.cumsum()
    drawdown = _compute_drawdown(equity_curve)
    max_drawdown = float(drawdown.min()) if not drawdown.empty else 0.0
    
    # Safe ROI Calculation
    roi = (total_pnl / initial_capital * 100) if initial_capital > 0 else 0.0

    return pd.Series(
        {
            "Total_PnL": total_pnl,
            "Total_Trades": total_trades,
            "Win_Rate": win_rate,
            "Loss_Rate": loss_rate,
            "Average_Win": average_win,
            "Average_Loss": average_loss,
            "Win_Loss_Ratio": win_loss_ratio,
            "Trade_Expectancy": expectancy,
            "Profit_Factor": profit_factor,
            "Sharpe_Ratio": sharpe_ratio,
            "Volatility": annual_volatility,
            "Max_Drawdown": max_drawdown,
            "ROI": roi,
        }
    )


def summarize_portfolios(trades_df: pd.DataFrame, initial_capital: float = 100000.0) -> pd.DataFrame:
    """Compute portfolio metrics for each Port_IDs with error handling."""
    # Debug Logs
    print(f"DEBUG: trades_df.shape = {getattr(trades_df, 'shape', 'N/A')}")
    print(f"DEBUG: initial_capital = {initial_capital} (Type: {type(initial_capital)})")
    
    if not isinstance(trades_df, pd.DataFrame) or trades_df.empty:
        logging.warning("summarize_portfolios: Empty or invalid trades_df")
        return pd.DataFrame()

    try:
        # Check if Port_IDs exist
        if "Port_IDs" not in trades_df.columns:
             st.error("Data error: 'Port_IDs' column missing. Metrics cannot be grouped.")
             return pd.DataFrame()
             
        # Groupby and apply - Removed include_groups=False for compatibility with older Pandas (2.0.x)
        result = trades_df.groupby("Port_IDs").apply(
            lambda x: portfolio_summary(x, initial_capital)
        ).reset_index()
        return result
    except Exception as e:
        st.error(f"Metric Calculation Error: {str(e)}")
        logging.exception("summarize_portfolios failed")
        return pd.DataFrame()


def build_time_analytics(trades_df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Build daily and hourly time-series analytics from trade history."""
    df = trades_df.copy()
    df["date"] = df["time"].dt.date
    df["hour"] = df["time"].dt.hour
    df["weekday"] = df["time"].dt.day_name()

    daily = (
        df.groupby("date")["realizedProfit"]
        .agg(Total_PnL="sum", Trade_Count="count")
        .assign(Cumulative_PnL=lambda x: x["Total_PnL"].cumsum())
        .reset_index()
    )

    hourly = (
        df.groupby("hour")["realizedProfit"]
        .agg(Total_PnL="sum", Trade_Count="count", Average_PnL="mean")
        .reset_index()
    )

    heatmap = (
        df.groupby(["weekday", "hour"])["realizedProfit"]
        .sum()
        .reset_index()
    )

    return {"daily": daily, "hourly": hourly, "heatmap": heatmap}


def build_strategy_performance(trades_df: pd.DataFrame) -> pd.DataFrame:
    """Compute performance by symbol, side, and position type."""
    performance = (
        trades_df.groupby(["symbol", "side", "positionSide"])["realizedProfit"]
        .agg(Total_PnL="sum", Trade_Count="count", Average_PnL="mean")
        .reset_index()
        .sort_values(by="Total_PnL", ascending=False)
    )
    return performance


def calculate_portfolio_metrics(trades_df: pd.DataFrame, initial_capital: float = 100000.0) -> dict[str, float]:
    """Return headline performance metrics for the entire trade dataset.
    
    Args:
        trades_df: DataFrame with trade data
        initial_capital: Initial trading capital in USDT (default 100,000)
    
    Returns:
        Dictionary with Total_PnL, ROI, Win_Rate, Total_Trades
    """
    total_pnl = float(trades_df["realizedProfit"].sum())
    roi = float((total_pnl / initial_capital) * 100) if initial_capital != 0 else 0.0
    wins = trades_df[trades_df["realizedProfit"] > 0]
    total_trades = len(trades_df)
    win_rate = float(len(wins) / total_trades * 100) if total_trades else 0.0
    return {
        "Total_PnL": total_pnl,
        "ROI": roi,
        "Win_Rate": win_rate,
        "Total_Trades": total_trades,
        "Initial_Capital": initial_capital,
    }


def summarize_symbol_performance(trades_df: pd.DataFrame, initial_capital: float = 100000.0) -> pd.DataFrame:
    """Return symbol-level performance metrics for coin comparison.
    
    ROI is calculated as: (Total_PnL / Initial_Capital) * 100
    to show each symbol's contribution to total portfolio performance.
    """
    symbol_summary = (
        trades_df.groupby("symbol")
        .apply(lambda x: pd.Series({
            "Total_PnL": x["realizedProfit"].sum(),
            "Trade_Count": len(x),
            "Average_PnL": x["realizedProfit"].mean() if not x.empty else 0.0,
            "ROI": float((x["realizedProfit"].sum() / initial_capital * 100) if initial_capital > 0 else 0.0),
        }))
        .reset_index()
        .sort_values(by="Total_PnL", ascending=False)
    )
    return symbol_summary


def detect_overtrading(trades_df: pd.DataFrame, threshold_per_hour: int = 20) -> pd.DataFrame:
    """Detect portfolios that execute a large number of trades in a short time window."""
    hourly_counts = (
        trades_df.set_index("time")
        .groupby("Port_IDs")
        .resample("1H")["realizedProfit"]
        .count()
        .reset_index(name="Trades_Per_Hour")
    )
    return hourly_counts[hourly_counts["Trades_Per_Hour"] >= threshold_per_hour].sort_values(
        ["Trades_Per_Hour", "Port_IDs"], ascending=[False, True]
    )


def detect_anomalies(trades_df: pd.DataFrame, zscore_threshold: float = 3.0) -> pd.DataFrame:
    """Identify suspicious or anomalous trade outcomes."""
    df = trades_df.copy()
    profit_std = df["realizedProfit"].std(ddof=0)
    profit_mean = df["realizedProfit"].mean()
    if profit_std == 0 or np.isnan(profit_std):
        return df.iloc[0:0]

    df["profit_zscore"] = (df["realizedProfit"] - profit_mean) / profit_std
    df["fee_ratio"] = np.where(df["trade_value"] > 0, np.abs(df["fee"] / df["trade_value"]), 0.0)
    anomalies = df[(df["profit_zscore"].abs() >= zscore_threshold) | (df["fee_ratio"] > 0.02)]
    return anomalies.sort_values(by=["profit_zscore", "fee_ratio"], ascending=False)
