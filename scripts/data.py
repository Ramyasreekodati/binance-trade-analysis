from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any, Sequence, cast

import numpy as np
import pandas as pd
from pandas._libs.tslibs.nattype import NaTType

DEFAULT_COLUMNS = ["Port_IDs", "Trade_History", "time", "symbol", "side", "price", "quantity", "realizedProfit"]


def load_trade_data(source: Any) -> pd.DataFrame:
    """Load trade data from a CSV file, uploaded file-like object, or a DataFrame."""
    if isinstance(source, pd.DataFrame):
        return source.copy()
    if isinstance(source, (str, Path)):
        return pd.read_csv(source)
    if hasattr(source, "read"):
        return pd.read_csv(source)
    raise ValueError("Source must be a file path, uploaded file-like object, or pandas DataFrame.")


def parse_trade_history(raw_value: Any) -> list[dict[str, Any]]:
    """Parse a Binance trade history string into a list of trade dictionaries."""
    if raw_value is None or raw_value == "" or raw_value is pd.NA or (
        isinstance(raw_value, float) and np.isnan(raw_value)
    ):
        return []

    if isinstance(raw_value, str):
        try:
            trades = ast.literal_eval(raw_value)
        except (ValueError, SyntaxError):
            try:
                trades = json.loads(raw_value)
            except Exception:
                return []
    elif isinstance(raw_value, (list, tuple)):
        trades: list[dict[str, Any]] = []
        for item in raw_value:
            if isinstance(item, dict):
                trades.append(item)
    else:
        return []

    parsed = []
    for trade in trades:
        if not isinstance(trade, dict):
            continue
        parsed.append(
            {
                "time": trade.get("time"),
                "symbol": trade.get("symbol"),
                "side": trade.get("side"),
                "price": trade.get("price"),
                "quantity": trade.get("quantity"),
                "realizedProfit": trade.get("realizedProfit"),
                "fee": trade.get("fee"),
                "positionSide": trade.get("positionSide"),
                "activeBuy": trade.get("activeBuy"),
            }
        )
    return parsed


def coerce_timestamp(value: Any) -> pd.Timestamp | NaTType:
    """Coerce a numeric or string timestamp into pandas Timestamp."""
    if value is None or value is pd.NA or (isinstance(value, float) and np.isnan(value)):
        return pd.NaT
    if isinstance(value, (int, float)):
        if value > 1e12:
            return pd.to_datetime(value, unit="ms", errors="coerce")
        return pd.to_datetime(value, unit="s", errors="coerce")
    return pd.to_datetime(value, errors="coerce")


def explode_trade_history(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Build a normalized trade table from nested Trade_History records."""
    df = raw_df.copy()
    if "Trade_History" not in df.columns:
        return df

    df["Parsed_Trades"] = df["Trade_History"].map(parse_trade_history)
    exploded = df.explode("Parsed_Trades", ignore_index=True)
    parsed = pd.json_normalize(exploded["Parsed_Trades"].tolist())
    parsed["Port_IDs"] = exploded["Port_IDs"].tolist()
    return parsed


def clean_trade_data(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Clean raw Binance trade data and produce a normalized trade table."""
    df = raw_df.copy()
    if "Trade_History" in df.columns:
        df = explode_trade_history(df)

    required_columns = {"Port_IDs", "time", "symbol", "side", "price", "quantity", "realizedProfit"}
    if not required_columns.issubset(df.columns):
        missing = required_columns.difference(df.columns)
        raise ValueError(f"Missing required trade columns: {missing}")

    df["time"] = df["time"].map(coerce_timestamp)
    df["symbol"] = df["symbol"].astype(str).str.upper().str.strip()
    df["side"] = df["side"].astype(str).str.upper().str.strip()
    df["side"] = df["side"].replace({"BUY": "BUY", "SELL": "SELL"})
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["realizedProfit"] = pd.to_numeric(df["realizedProfit"], errors="coerce")

    if "fee" in df.columns:
        df["fee"] = pd.to_numeric(df["fee"], errors="coerce").fillna(0.0)
    else:
        df["fee"] = 0.0

    if "positionSide" in df.columns:
        df["positionSide"] = df["positionSide"].astype(str).str.upper()
    else:
        df["positionSide"] = ""

    if "activeBuy" in df.columns:
        df["activeBuy"] = df["activeBuy"].astype(bool)
    else:
        df["activeBuy"] = False

    df = df.drop_duplicates(subset=["Port_IDs", "time", "symbol", "side", "price", "quantity", "realizedProfit"])
    df = df.dropna(subset=["Port_IDs", "time", "symbol", "side", "price", "quantity", "realizedProfit"])
    df = df[(df["price"] > 0) & (df["quantity"] > 0)]

    df["investment"] = df["price"] * df["quantity"]
    df["trade_value"] = (df["price"] * df["quantity"]).abs()
    df = df.sort_values(["Port_IDs", "time"]).reset_index(drop=True)
    return df


def validation_report(df: pd.DataFrame) -> dict[str, Any]:
    """Return a summary of missing values and duplicate records for a trade DataFrame."""
    report = {
        "missing_values": df.isna().sum().to_dict(),
        "duplicate_records": int(df.duplicated().sum()),
        "records": len(df),
    }
    return report
