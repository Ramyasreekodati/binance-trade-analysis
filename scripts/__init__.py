"""Binance trade analysis package."""

from .data import load_trade_data, clean_trade_data
from .metrics import (
    summarize_portfolios,
    build_time_analytics,
    build_strategy_performance,
    detect_overtrading,
    detect_anomalies,
)
from .visualization import (
    plot_equity_curve,
    plot_drawdown_curve,
    plot_profit_distribution,
    plot_profitability_heatmap,
)
from .insights import generate_insights
from .backtest import StrategyBacktester
