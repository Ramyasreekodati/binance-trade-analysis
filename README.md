# Binance Trade Analytics & Risk Intelligence

A portfolio-grade trading analytics system built to transform Binance trade history into a professional risk intelligence dashboard.

## Overview

This project converts raw Binance execution data into a clean, validated analytics platform with real trading metrics, strategy evaluation, anomaly detection, and an interactive Streamlit dashboard.

## Problem Statement

Trading performance is not just about gross profit — it is about risk, edge, trade quality, and stability. This system helps traders and analysts understand where profits come from, when risk concentrates, and which signals are most reliable.

## Features

- Clean and validate Binance trade data
- Normalize nested trade-history payloads into a structured trade table
- Compute mandatory financial metrics:
  - Profit & Loss (PnL)
  - Sharpe Ratio
  - Maximum Drawdown
  - Win/Loss Ratio
  - Trade Expectancy
  - Volatility
- Advanced analytics:
  - Strategy performance evaluation by symbol and side
  - Time-based profitability analysis (hourly/daily)
  - Overtrading detection
  - Pattern and anomaly detection
- Professional visualizations:
  - Equity curve
  - Drawdown curve
  - Profit distribution histogram
  - Profitability heatmap
- Interactive Streamlit app for dynamic reporting
- Modular code structure for production readiness
- Bonus backtesting utilities for directional and hourly edge analysis

## Tech Stack

- Python 3.11+
- pandas, NumPy
- Streamlit
- Plotly
- scikit-learn
- SciPy
- seaborn

## Installation

```bash
python -m pip install -r requirements.txt
```

## Run the analysis pipeline

```bash
python scripts/run_analysis.py
```

This generates CSV outputs in the `outputs/` folder:
- `parsed_trades.csv`
- `portfolio_metrics.csv`
- `strategy_performance.csv`
- `anomaly_trades.csv`
- `overtrading_events.csv`
- `top_20_portfolios.csv`
- `generated_insights.txt`
- `validation_report.txt`

## Run the interactive dashboard

```bash
streamlit run streamlit_app.py
```

The app supports file upload and automatically loads `TRADES_CopyTr_90D_ROI.csv` if present.

## Key Insights Delivered

- High-volatility periods often coincide with elevated loss frequency.
- Consecutive losing streaks degrade win rate and highlight the need for risk filters.
- Symbols and trade directions are ranked by profitability to reveal the strongest edges.
- Overtrading alerts identify portfolios that may be accumulating execution risk too quickly.

## Project Structure

- `scripts/data.py` — data ingestion, cleaning, normalization, and validation
- `scripts/metrics.py` — financial metrics, risk, and time-based analytics
- `scripts/visualization.py` — production-ready chart builders for Streamlit
- `scripts/insights.py` — automated insight generation from trade patterns
- `scripts/backtest.py` — basic signal and edge backtesting utilities
- `scripts/run_analysis.py` — batch pipeline for exporting analytics artifacts
- `streamlit_app.py` — interactive dashboard for analysts and traders
- `requirements.txt` — Python dependencies

## Notes

This system is designed for analysts who need a reproducible trading intelligence workflow with clean code, modular components, and dynamic visualization.
