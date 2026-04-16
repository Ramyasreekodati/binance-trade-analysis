from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st


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
    if symbol is None or symbol == "All symbols":
        # If no symbol specified, use the most frequently traded symbol to avoid price mixing
        if not df.empty:
            symbol = df["symbol"].value_counts().idxmax()
            df = df[df["symbol"] == symbol]
    else:
        df = df[df["symbol"] == symbol]

    if df.empty:
        return pd.DataFrame()

    df = df.sort_values("time").set_index("time")
    timeframe_norm = normalize_timeframe(timeframe)
    timeframe_norm = timeframe_norm.replace("T", "min").replace("H", "h")
    
    # Use mean price per period instead of just last to reduce noise
    price_series = df["price"].resample(timeframe_norm).mean().ffill().dropna()
    return price_series.to_frame(name="close")


@st.cache_data(show_spinner=True)
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


TIMEFRAME_ALIAS = {
    "5m": "5T",
    "1h": "1H",
    "1d": "1D",
}


def normalize_timeframe(timeframe: str) -> str:
    """Normalize friendly timeframe labels to pandas resampling frequency."""
    return TIMEFRAME_ALIAS.get(timeframe.lower(), timeframe)


def build_market_insight(
    trades_df: pd.DataFrame,
    timeframe: str = "1H",
    symbol: str | None = None,
) -> dict[str, str]:
    """Build a concise market insight card for the selected symbol and timeframe."""
    indicator_df = build_timeframe_indicators(trades_df, timeframe, symbol)
    if indicator_df.empty:
        return {
            "signal": "No data",
            "trend": "No data",
            "rsi": "No data",
            "action": "No action",
            "reason": "Not enough trade history to generate an insight.",
        }

    latest = indicator_df.iloc[-1]
    trend = "Bullish" if latest["ema_short"] >= latest["ema_long"] else "Bearish"
    rsi_value = float(latest["rsi"])
    if rsi_value > 70:
        rsi_state = "Overbought"
    elif rsi_value < 30:
        rsi_state = "Oversold"
    else:
        rsi_state = "Neutral"

    action = latest["signal"]
    reason = (
        f"{action} signal based on a {trend.lower()} trend and RSI at {rsi_value:.1f} ({rsi_state}). "
        "The moving average crossover gives direction, while RSI filters the entry timing."
    )

    return {
        "signal": action,
        "trend": trend,
        "rsi": f"{rsi_value:.1f} ({rsi_state})",
        "action": action,
        "reason": reason,
    }


def build_signal_backtest_summary(
    trades_df: pd.DataFrame,
    timeframe: str = "1H",
    symbol: str | None = None,
) -> dict[str, float]:
    """Build a quick signal-based backtest summary using price series from trade history."""
    symbol_to_use = symbol
    if symbol == "All symbols":
        symbol_to_use = None
        
    price_df = _build_price_series(trades_df, timeframe, symbol_to_use)
    if price_df.empty or len(price_df) < 2:
        return {
            "Cumulative_Return": 0.0,
            "Max_Drawdown": 0.0,
            "Signals": 0,
        }

    indicator_df = build_timeframe_indicators(trades_df, timeframe, symbol_to_use)
    indicator_df = indicator_df.set_index("time").sort_index()
    
    # Prevent look-ahead bias by shifting signal
    indicator_df["position"] = (indicator_df["signal"] == "Buy").astype(int)
    indicator_df["returns"] = indicator_df["close"].pct_change().fillna(0.0)
    
    # Cap returns to avoid extreme data jitter causing -100% bug
    indicator_df["returns"] = indicator_df["returns"].clip(-0.5, 0.5)
    
    indicator_df["strategy_returns"] = indicator_df["returns"] * indicator_df["position"].shift(1).fillna(0.0)
    
    # Calculate equity using cumulative sum of log returns for better stability, or simple sum for small returns
    equity = (1 + indicator_df["strategy_returns"]).cumprod()
    
    if equity.empty:
        return {"Cumulative_Return": 0.0, "Max_Drawdown": 0.0, "Signals": 0}
        
    drawdown = (equity / equity.cummax() - 1).fillna(0.0)

    return {
        "Cumulative_Return": float((equity.iloc[-1] - 1) * 100),
        "Max_Drawdown": float(drawdown.min() * 100),
        "Signals": int((indicator_df["signal"] != "Hold").sum()),
    }


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
