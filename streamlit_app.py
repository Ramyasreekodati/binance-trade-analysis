from pathlib import Path

import pandas as pd
import streamlit as st

from scripts.backtest import StrategyBacktester
from scripts.data import clean_trade_data, load_trade_data, validation_report
from scripts.insights import generate_insights
from scripts.metrics import (
    build_strategy_performance,
    build_time_analytics,
    calculate_portfolio_metrics,
    detect_anomalies,
    detect_overtrading,
    summarize_portfolios,
    summarize_symbol_performance,
)
from scripts.strategy import (
    build_market_insight,
    build_signal_backtest_summary,
    build_timeframe_indicators,
    compare_timeframe_trends,
    generate_timeframe_summary,
    strategy_explanation_text,
)
from scripts.visualization import (
    plot_drawdown_curve,
    plot_equity_curve,
    plot_profit_distribution,
    plot_profitability_heatmap,
)

DEFAULT_SOURCE = Path("TRADES_CopyTr_90D_ROI.csv")


@st.cache_data(show_spinner=False)
def load_default_dataset() -> pd.DataFrame:
    return load_trade_data(DEFAULT_SOURCE)


def load_data() -> pd.DataFrame:
    if DEFAULT_SOURCE.exists():
        st.sidebar.info(f"Using default dataset: {DEFAULT_SOURCE.name}")
        uploaded = st.sidebar.file_uploader(
            "Upload Binance trade CSV to override default dataset (optional)",
            type=["csv"],
        )
        if uploaded is not None:
            df = load_trade_data(uploaded)
            st.sidebar.success("Uploaded file loaded successfully.")
            return df

        with st.spinner("Loading default dataset..."):
            return load_default_dataset()

    uploaded = st.sidebar.file_uploader("Upload Binance trade CSV", type=["csv"])
    if uploaded is not None:
        df = load_trade_data(uploaded)
        st.sidebar.success("File uploaded successfully.")
        return df

    st.sidebar.warning("Upload a trade file or add TRADES_CopyTr_90D_ROI.csv to the project root.")
    return pd.DataFrame()


def format_portfolio_selector(metrics_df: pd.DataFrame) -> list[str]:
    values = ["All portfolios"]
    values.extend(metrics_df["Port_IDs"].astype(str).tolist())
    return values


def main() -> None:
    st.set_page_config(page_title="Binance Trade Analytics", page_icon="📈", layout="wide")
    st.title("Binance Trade Analytics & Risk Intelligence")
    st.markdown(
        "A professional dashboard for trading analytics, risk intelligence, strategy evaluation, and anomaly detection built on Binance execution data."
    )

    raw_df = load_data()
    if raw_df.empty:
        st.warning("No trade data available. Upload a valid Binance trade CSV or add the default dataset file.")
        st.stop()

    with st.spinner("Cleaning trade data and building analytics..."):
        trades = clean_trade_data(raw_df)
        validation = validation_report(trades)
        metrics_df = summarize_portfolios(trades)
        portfolio_metrics = calculate_portfolio_metrics(trades)
        symbol_performance = summarize_symbol_performance(trades)
        time_analytics = build_time_analytics(trades)
        strategy_df = build_strategy_performance(trades)
        anomalies_df = detect_anomalies(trades)
        overtrading_df = detect_overtrading(trades)
        insights = generate_insights(trades, metrics_df)
        backtester = StrategyBacktester(trades)

    selected_portfolio = st.sidebar.selectbox(
        "Select portfolio", format_portfolio_selector(metrics_df)
    )
    selected_timeframe_label = st.sidebar.selectbox(
        "Select timeframe", ["5m", "1h", "1d"], index=1
    )
    selected_symbol = st.sidebar.selectbox(
        "Choose symbol for comparison", ["All symbols"] + sorted(trades["symbol"].unique().astype(str).tolist()))
    show_anomalies = st.sidebar.checkbox("Show anomaly trade table", value=True)
    show_strategy = st.sidebar.checkbox("Show strategy evaluation", value=True)
    show_backtest = st.sidebar.checkbox("Show backtest diagnostics", value=True)

    filtered_portfolio = None
    if selected_portfolio != "All portfolios":
        filtered_portfolio = int(selected_portfolio)

    timeframe_map = {"5m": "5m", "1h": "1h", "1d": "1d"}
    selected_timeframe = timeframe_map[selected_timeframe_label]
    selected_symbol_filter = None if selected_symbol == "All symbols" else selected_symbol
    timeframe_signals = generate_timeframe_summary(
        trades,
        ["5m", "1h", "1d"],
        selected_symbol_filter,
    )
    market_insight = build_market_insight(trades, selected_timeframe, selected_symbol_filter)
    backtest_summary = build_signal_backtest_summary(trades, selected_timeframe, selected_symbol_filter)

    st.header("Market Overview 🧭")
    overview_col1, overview_col2, overview_col3, overview_col4 = st.columns(4)
    overview_col1.metric("Net Realized PnL", f"{portfolio_metrics['Total_PnL']:,.2f} USDT")
    overview_col2.metric("ROI", f"{portfolio_metrics['ROI']:.2f}%")
    overview_col3.metric("Win Rate", f"{portfolio_metrics['Win_Rate']:.1f}%")
    overview_col4.metric("Total Trades", f"{portfolio_metrics['Total_Trades']}")

    st.markdown("---")
    st.subheader("Market Insight & Recommendation")
    insight_col1, insight_col2, insight_col3, insight_col4 = st.columns([1, 1, 1, 2])
    insight_col1.metric("Signal", market_insight["signal"])
    insight_col2.metric("Trend", market_insight["trend"])
    insight_col3.metric("RSI", market_insight["rsi"])
    insight_col4.metric("Recommended Action", market_insight["action"])
    st.info(market_insight["reason"])

    st.markdown("---")
    st.subheader("Decision Intelligence")
    st.write(
        "This section translates technical indicators into a clear recommendation, so the dashboard becomes actionable rather than just visual."
    )
    st.dataframe(timeframe_signals, use_container_width=True)

    selected_indicators = build_timeframe_indicators(trades, selected_timeframe, selected_symbol_filter)
    if not selected_indicators.empty:
        st.subheader("Charts & Indicators")
        st.write(
            f"Viewing {selected_symbol if selected_symbol_filter else 'all available symbols'} on the {selected_timeframe_label} timeframe."
        )
        st.line_chart(
            selected_indicators.set_index("time")[['close', 'ema_short', 'ema_long']],
            use_container_width=True,
        )
        st.line_chart(
            selected_indicators.set_index("time")[["rsi"]],
            use_container_width=True,
        )

    if selected_symbol_filter:
        st.markdown(f"**Trend comparison for {selected_symbol_filter}:**")
        st.dataframe(
            compare_timeframe_trends(trades, [selected_symbol_filter], ["5m", "1h", "1d"]),
            use_container_width=True,
        )

    st.subheader("Backtest Snapshot")
    backtest_col1, backtest_col2, backtest_col3 = st.columns(3)
    backtest_col1.metric("Signal Count", f"{backtest_summary['Signals']}")
    backtest_col2.metric("Backtest Return", f"{backtest_summary['Cumulative_Return']:.2f}%")
    backtest_col3.metric("Max Drawdown", f"{backtest_summary['Max_Drawdown']:.2f}%")

    st.subheader("Symbol Comparison")
    st.write("Review top coins by realized profit and average trade performance.")
    st.dataframe(symbol_performance.head(15), use_container_width=True)

    csv = trades.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download cleaned trade dataset",
        csv,
        "binance_trade_analysis.csv",
        "text/csv",
        key="download-data",
    )

    with st.expander("Data validation summary"):
        st.json(validation)

    st.subheader("Equity and Risk Curves")
    equity_fig = plot_equity_curve(trades, filtered_portfolio)
    drawdown_fig = plot_drawdown_curve(trades, filtered_portfolio)
    st.plotly_chart(equity_fig, use_container_width=True)
    st.plotly_chart(drawdown_fig, use_container_width=True)

    st.subheader("Profitability Distribution")
    profit_fig = plot_profit_distribution(trades)
    st.plotly_chart(profit_fig, use_container_width=True)

    st.subheader("Timing and Volatility Heatmap")
    heatmap_fig = plot_profitability_heatmap(trades)
    st.plotly_chart(heatmap_fig, use_container_width=True)

    st.subheader("Key Insights")
    for insight in insights:
        st.write(f"- {insight}")

    st.subheader("Strategy Explanation 🧠")
    st.markdown(strategy_explanation_text())

    if show_strategy:
        st.subheader("Strategy & Pattern Performance")
        st.write("Top symbol-side combinations by realized profit")
        st.dataframe(strategy_df.head(15), use_container_width=True)

        st.markdown("**Hourly performance edge**")
        side_edge = backtester.hourly_edge()
        st.dataframe(side_edge, use_container_width=True)

    if show_backtest:
        st.subheader("Backtest Diagnostics")
        st.write("Evaluate the directional edge and trade timing performance.")
        st.write(backtester.side_edge())
        st.write(backtester.symbol_edge().head(12))

    if show_anomalies and not anomalies_df.empty:
        st.subheader("Anomaly Detection")
        st.write(
            "Trades flagged for unusually large profits/losses or elevated fee ratios. Review these events for suspicious behavior or risk concentration."
        )
        st.dataframe(anomalies_df["time symbol side realizedProfit fee fee_ratio profit_zscore Port_IDs".split()].head(20), use_container_width=True)

    if not overtrading_df.empty:
        st.subheader("Overtrading Alert")
        st.write(
            "Portfolios that executed a high number of trades in a single hourly window, which may indicate risk accumulation."
        )
        st.dataframe(overtrading_df.head(20), use_container_width=True)

    st.sidebar.markdown("---")
    st.sidebar.markdown("Built for portfolio-grade trading analytics and production-level reporting.")


if __name__ == "__main__":
    main()
