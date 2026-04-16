from __future__ import annotations

import numpy as np
import pandas as pd


def _compute_ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def _compute_rsi(prices: pd.Series, window: int = 14) -> pd.Series:
    delta = prices.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.rolling(window=window, min_periods=window).mean()
    avg_loss = loss.rolling(window=window, min_periods=window).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50.0)


def _build_price_series(trades_df: pd.DataFrame, timeframe: str, symbol: str | None = None) -> pd.DataFrame:
    df = trades_df.copy()
    if symbol is not None:
        df = df[df["symbol"] == symbol]

    if df.empty:
        return pd.DataFrame()

    df = df.sort_values("time").set_index("time")
    price_series = df["price"].resample(timeframe).last().ffill().dropna()
    return price_series.to_frame(name="close")


def build_timeframe_indicators(
    trades_df: pd.DataFrame,
    timeframe: str = "1H",
    symbol: str | None = None,
) -> pd.DataFrame:
    price_df = _build_price_series(trades_df, timeframe, symbol)
    if price_df.empty:
        return pd.DataFrame()

    price_df["ema_short"] = _compute_ema(price_df["close"], span=12)
    price_df["ema_long"] = _compute_ema(price_df["close"], span=26)
    price_df["rsi"] = _compute_rsi(price_df["close"], window=14)

    price_df["signal"] = np.where(
        (price_df["ema_short"] > price_df["ema_long"]) & (price_df["rsi"] < 70),
        "Buy",
        np.where(
            (price_df["ema_short"] < price_df["ema_long"]) & (price_df["rsi"] > 30),
            "Sell",
            "Hold",
        ),
    )
    price_df["explanation"] = price_df.apply(_signal_explanation, axis=1)
    return price_df.reset_index()


def _signal_explanation(row: pd.Series) -> str:
    if row["signal"] == "Buy":
        return (
            "Short-term momentum is rising and RSI is below the overbought zone, "
            "suggesting a favorable entry opportunity."
        )
    if row["signal"] == "Sell":
        return (
            "Short-term momentum is weakening while RSI is above the healthy range, "
            "suggesting it may be time to lock in profits."
        )
    return "Market momentum is mixed, so preserve capital until the next clear signal."


def generate_timeframe_summary(
    trades_df: pd.DataFrame,
    timeframes: list[str] = ["5T", "1H", "1D"],
    symbol: str | None = None,
) -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    for timeframe in timeframes:
        indicator_df = build_timeframe_indicators(trades_df, timeframe, symbol)
        if indicator_df.empty:
            rows.append(
                {
                    "Timeframe": timeframe,
                    "Signal": "No data",
                    "Trend": "No data",
                    "Explanation": "Not enough trade history to build this timeframe.",
                }
            )
            continue

        latest = indicator_df.iloc[-1]
        trend = "Bullish" if latest["ema_short"] >= latest["ema_long"] else "Bearish"
        rows.append(
            {
                "Timeframe": timeframe,
                "Signal": latest["signal"],
                "Trend": trend,
                "Explanation": latest["explanation"],
            }
        )
    return pd.DataFrame(rows)


def compare_timeframe_trends(trades_df: pd.DataFrame, symbols: list[str], timeframes: list[str]) -> pd.DataFrame:
    rows: list[dict[str, str | int]] = []
    for symbol in symbols:
        for timeframe in timeframes:
            indicator_df = build_timeframe_indicators(trades_df, timeframe, symbol)
            if indicator_df.empty:
                rows.append({"symbol": symbol, "timeframe": timeframe, "trend": "No data"})
                continue
            latest = indicator_df.iloc[-1]
            trend = "Bullish" if latest["ema_short"] >= latest["ema_long"] else "Bearish"
            rows.append({"symbol": symbol, "timeframe": timeframe, "trend": trend})
    return pd.DataFrame(rows)


def strategy_explanation_text() -> str:
    return (
        "This strategy combines two common technical tools for robust trade analysis:\n"
        "1. Exponential Moving Averages (EMA): the 12-period EMA reacts quickly to price moves, "
        "while the 26-period EMA helps identify the broader trend. A bullish crossover suggests upward momentum, "
        "and a bearish crossover suggests downward momentum.\n\n"
        "2. Relative Strength Index (RSI): measures the strength of recent price action. "
        "Values below 30 are often oversold, values above 70 are often overbought, and values in the middle suggest consolidation.\n\n"
        "A signal is generated when the short-term EMA crosses the long-term EMA, filtered by RSI for better entry and exit timing."
    )
