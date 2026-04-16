from __future__ import annotations

import pandas as pd


def _build_performance_table(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby(df["time"].dt.to_period("D"))["realizedProfit"]
        .agg(Total_PnL="sum", Trade_Count="count", Average_PnL="mean")
        .reset_index()
    )


class StrategyBacktester:
    """Basic backtest utilities for trade event analysis."""

    def __init__(self, trades_df: pd.DataFrame) -> None:
        self.trades = trades_df.copy()
        self.trades["hour"] = self.trades["time"].dt.hour

    def side_edge(self) -> pd.DataFrame:
        """Calculate directional edge for BUY and SELL trade sides."""
        summary = (
            self.trades.groupby("side")["realizedProfit"]
            .agg(Total_PnL="sum", Trade_Count="count", Average_PnL="mean")
            .reset_index()
        )
        return summary.sort_values(by="Total_PnL", ascending=False)

    def hourly_edge(self) -> pd.DataFrame:
        """Evaluate average profitability for each trading hour."""
        summary = (
            self.trades.groupby("hour")["realizedProfit"]
            .agg(Total_PnL="sum", Trade_Count="count", Average_PnL="mean")
            .reset_index()
            .sort_values(by="Total_PnL", ascending=False)
        )
        return summary

    def symbol_edge(self, min_trades: int = 10) -> pd.DataFrame:
        """Rank symbols by their trade performance for signal selection."""
        symbol_performance = (
            self.trades.groupby("symbol")["realizedProfit"]
            .agg(Total_PnL="sum", Trade_Count="count", Average_PnL="mean")
            .reset_index()
        )
        return symbol_performance[symbol_performance["Trade_Count"] >= min_trades].sort_values(
            by="Total_PnL", ascending=False
        )

    def daily_trading_profile(self) -> pd.DataFrame:
        """Return daily PnL and trade count for simple backtest diagnostics."""
        return _build_performance_table(self.trades)
