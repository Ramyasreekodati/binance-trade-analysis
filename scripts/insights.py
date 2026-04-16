from __future__ import annotations

import pandas as pd

from .metrics import detect_overtrading


def _group_outcome_sequences(trades: pd.DataFrame, min_length: int = 3) -> pd.DataFrame:
    records = []
    for port_id, group in trades.sort_values("time").groupby("Port_IDs"):
        sequence_type = None
        sequence_length = 0
        sequence_profit = 0.0
        for pnl in group["realizedProfit"]:
            direction = "win" if pnl > 0 else "loss" if pnl < 0 else "neutral"
            if sequence_type is None or direction == sequence_type:
                sequence_type = direction
                sequence_length += 1
                sequence_profit += pnl
            else:
                if sequence_type == "loss" and sequence_length >= min_length:
                    records.append(
                        {
                            "Port_IDs": port_id,
                            "Sequence_Length": sequence_length,
                            "Sequence_Type": sequence_type,
                            "Sequence_Profit": sequence_profit,
                        }
                    )
                sequence_type = direction
                sequence_length = 1
                sequence_profit = pnl

        if sequence_type == "loss" and sequence_length >= min_length:
            records.append(
                {
                    "Port_IDs": port_id,
                    "Sequence_Length": sequence_length,
                    "Sequence_Type": sequence_type,
                    "Sequence_Profit": sequence_profit,
                }
            )

    return pd.DataFrame(records)


def generate_insights(trades_df: pd.DataFrame, metrics_df: pd.DataFrame) -> list[str]:
    """Generate actionable insights from trade and portfolio performance data."""
    insights: list[str] = []
    if trades_df.empty:
        return ["No trade data loaded for insight generation."]

    total_profit = float(trades_df["realizedProfit"].sum())
    average_trade = float(trades_df["realizedProfit"].mean())
    high_volatility = trades_df["realizedProfit"].std(ddof=0) > trades_df["realizedProfit"].abs().mean()

    if high_volatility:
        insights.append("Most losses occur during high-volatility periods or when trade outcomes have wide profit variance.")
    if total_profit > 0:
        insights.append("The portfolio is net profitable, but there may still be opportunities to reduce drawdown and improve expectancy.")
    else:
        insights.append("The portfolio is currently loss-making, prioritize risk control and filter high-volatility entries.")

    overtrading = detect_overtrading(trades_df)
    if not overtrading.empty:
        insights.append(
            f"Overtrading detected: {overtrading['Port_IDs'].nunique()} portfolio(s) executed more than {overtrading['Trades_Per_Hour'].max()} trades in a single hour."
        )

    sequence_analysis = _group_outcome_sequences(trades_df)
    if not sequence_analysis.empty:
        longest_loss = int(sequence_analysis["Sequence_Length"].max())
        insights.append(
            f"Win rate drops significantly after sequences of consecutive losses, with the longest losing streak at {longest_loss} trades."
        )

    symbol_perf = (
        trades_df.groupby("symbol", as_index=False)["realizedProfit"]
        .agg(Total_PnL="sum", Trade_Count="count")
        .sort_values(by="Total_PnL", ascending=False)
        .reset_index(drop=True)
    )
    if not symbol_perf.empty:
        best_symbol = symbol_perf.loc[0, "symbol"]
        insights.append(f"Top performing symbol: {best_symbol} is driving the strongest profits.")
        if symbol_perf.loc[symbol_perf.index[-1], "Total_PnL"] < 0:
            insights.append("Some symbols are consistently loss-making and should be reviewed or excluded from active strategies.")

    if average_trade < 0:
        insights.append("The average trade is losing money. Focus on improving trade selection and risk per trade.")
    else:
        insights.append("A positive average trade indicates a constructive edge, but preserve it by limiting exposure during drawdowns.")

    return insights
