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
        st.sidebar.info(f"📊 Default dataset: {DEFAULT_SOURCE.name}")
        uploaded = st.sidebar.file_uploader(
            "Override with custom trade CSV (optional)",
            type=["csv"],
        )
        if uploaded is not None:
            df = load_trade_data(uploaded)
            st.sidebar.success("✓ Custom file loaded successfully.")
            return df

        with st.spinner("Loading default dataset..."):
            return load_default_dataset()

    uploaded = st.sidebar.file_uploader("Upload Binance trade CSV", type=["csv"])
    if uploaded is not None:
        df = load_trade_data(uploaded)
        st.sidebar.success("✓ File uploaded successfully.")
        return df

    st.sidebar.warning("⚠️ Upload a trade file or add TRADES_CopyTr_90D_ROI.csv to the project root.")
    return pd.DataFrame()


def format_portfolio_selector(metrics_df: pd.DataFrame) -> list[str]:
    values = ["All portfolios"]
    values.extend(metrics_df["Port_IDs"].astype(str).tolist())
    return values


def main() -> None:
    st.set_page_config(page_title="Binance Trade Analytics", page_icon="📈", layout="wide")
    st.title("📈 Binance Trade Analytics & Risk Intelligence")
    st.markdown(
        """
        Professional dashboard for trading analytics, risk management, strategy evaluation, and anomaly detection.
        Built on Binance execution data with production-level data validation and metrics accuracy.
        """
    )

    raw_df = load_data()
    if raw_df.empty:
        st.warning("No trade data available. Upload a valid Binance trade CSV or add the default dataset file.")
        st.stop()

    with st.spinner("Cleaning trade data and building analytics..."):
        trades = clean_trade_data(raw_df)
        validation = validation_report(trades)
        metrics_df = summarize_portfolios(trades)
        symbol_performance = summarize_symbol_performance(trades)
        time_analytics = build_time_analytics(trades)
        strategy_df = build_strategy_performance(trades)
        anomalies_df = detect_anomalies(trades)
        overtrading_df = detect_overtrading(trades)
        insights = generate_insights(trades, metrics_df)
        backtester = StrategyBacktester(trades)

    st.sidebar.markdown("---")
    st.sidebar.subheader("⚙️ Configuration")
    
    initial_capital = st.sidebar.number_input(
        "Initial Capital (USDT)",
        value=100000.0,
        min_value=1000.0,
        step=10000.0,
        help="Starting capital for ROI calculation. Default: 100,000 USDT"
    )
    
    selected_portfolio = st.sidebar.selectbox(
        "Select Portfolio", format_portfolio_selector(metrics_df)
    )
    selected_timeframe_label = st.sidebar.selectbox(
        "Select Timeframe", ["5m", "1h", "1d"], index=1
    )
    selected_symbol = st.sidebar.selectbox(
        "Choose Symbol for Analysis", ["All symbols"] + sorted(trades["symbol"].unique().astype(str).tolist()))
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("📋 Display Options")
    show_anomalies = st.sidebar.checkbox("Show Anomaly Detection", value=True)
    show_strategy = st.sidebar.checkbox("Show Strategy Analysis", value=True)
    show_backtest = st.sidebar.checkbox("Show Backtest Diagnostics", value=True)

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
    portfolio_metrics = calculate_portfolio_metrics(trades, initial_capital)

    st.header("📊 Market Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Net Realized PnL",
            f"{portfolio_metrics['Total_PnL']:,.2f} USDT",
            help="Sum of all realized profits and losses from trades"
        )
    
    with col2:
        st.metric(
            "ROI %",
            f"{portfolio_metrics['ROI']:.2f}%",
            help=f"Return on Investment based on {portfolio_metrics['Initial_Capital']:,.0f} USDT initial capital. Formula: (Net PnL / Initial Capital) * 100"
        )
    
    with col3:
        st.metric(
            "Win Rate",
            f"{portfolio_metrics['Win_Rate']:.1f}%",
            help="Percentage of profitable trades"
        )
    
    with col4:
        st.metric(
            "Total Trades",
            f"{portfolio_metrics['Total_Trades']:,}",
            help="Total number of trades executed"
        )

    st.markdown("---")
    st.subheader("🧭 Market Insight & Signal")
    
    insight_col1, insight_col2, insight_col3, insight_col4 = st.columns([1, 1, 1, 2])
    
    with insight_col1:
        st.metric("Signal", market_insight["signal"])
    with insight_col2:
        st.metric("Trend", market_insight["trend"])
    with insight_col3:
        st.metric("RSI", market_insight["rsi"])
    with insight_col4:
        st.metric("Action", market_insight["action"])
    
    st.info(
        f"💡 **Recommendation:** {market_insight['reason']}"
    )

    st.markdown("---")
    st.subheader("📍 Decision Intelligence - Multi-Timeframe Analysis")
    st.write("Technical signals across different timeframes to validate trade direction consistency.")
    
    signal_display = timeframe_signals.copy()
    st.dataframe(signal_display, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("📈 Technical Indicators")
    
    selected_indicators = build_timeframe_indicators(trades, selected_timeframe, selected_symbol_filter)
    if not selected_indicators.empty:
        st.write(
            f"Showing {selected_symbol if selected_symbol_filter else 'all available symbols'} on the {selected_timeframe_label} timeframe."
        )
        
        # Price and Moving Averages
        st.write("**Price Movement & Moving Averages**")
        price_chart_data = selected_indicators.set_index("time")[['close', 'ema_short', 'ema_long']]
        st.line_chart(price_chart_data, use_container_width=True)
        
        # RSI Indicator
        st.write("**Relative Strength Index (RSI)** - Overbought (>70) / Oversold (<30)")
        rsi_chart_data = selected_indicators.set_index("time")[["rsi"]]
        st.line_chart(rsi_chart_data, use_container_width=True)
    else:
        st.warning("No indicator data available for the selected timeframe and symbol.")

    if selected_symbol_filter:
        st.markdown("---")
        st.subheader(f"🔄 Trend Comparison - {selected_symbol_filter}")
        trend_data = compare_timeframe_trends(trades, [selected_symbol_filter], ["5m", "1h", "1d"])
        st.dataframe(trend_data, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("🎯 Backtest Snapshot")
    
    backtest_col1, backtest_col2, backtest_col3 = st.columns(3)
    
    with backtest_col1:
        st.metric(
            "Signal Count",
            f"{int(backtest_summary['Signals']):,}",
            help="Number of buy/sell signals generated by the strategy"
        )
    
    with backtest_col2:
        cumulative_return = backtest_summary['Cumulative_Return']
        st.metric(
            "Strategy Return",
            f"{cumulative_return:.2f}%",
            help="Cumulative return from following the strategy signals"
        )
    
    with backtest_col3:
        max_dd = backtest_summary['Max_Drawdown']
        st.metric(
            "Max Drawdown",
            f"{max_dd:.2f}%",
            help="Maximum peak-to-trough decline during the period"
        )

    st.markdown("---")
    st.subheader("💰 Symbol Performance Ranking")
    st.write("Top trading symbols by realized profit and trade count.")
    
    symbol_perf_display = symbol_performance.head(15).copy()
    symbol_perf_display["Total_PnL"] = symbol_perf_display["Total_PnL"].apply(lambda x: f"{x:,.2f}")
    symbol_perf_display["Average_PnL"] = symbol_perf_display["Average_PnL"].apply(lambda x: f"{x:,.2f}")
    symbol_perf_display["ROI"] = symbol_perf_display["ROI"].apply(lambda x: f"{x:.2f}%")
    symbol_perf_display = symbol_perf_display.rename(columns={"Trade_Count": "Trades"})
    
    st.dataframe(symbol_perf_display, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("⬇️ Download & Export")
    
    csv = trades.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Download Cleaned Trade Dataset (CSV)",
        csv,
        "binance_trade_analysis.csv",
        "text/csv",
        key="download-data",
    )

    with st.expander("📋 Data Validation Report", expanded=False):
        col1, col2, col3 = st.columns(3)
        col1.write(f"**Total Records:** {validation.get('records', 0):,}")
        col2.write(f"**Missing Values:** {len(validation.get('missing_values', {}))}")
        col3.write(f"**Duplicates:** {validation.get('duplicate_records', 0)}")
        st.json(validation)

    st.markdown("---")
    st.subheader("📊 Equity & Risk Analysis")
    
    equity_fig = plot_equity_curve(trades, filtered_portfolio)
    drawdown_fig = plot_drawdown_curve(trades, filtered_portfolio)
    
    st.plotly_chart(equity_fig, use_container_width=True)
    st.plotly_chart(drawdown_fig, use_container_width=True)

    st.subheader("📈 Profit Distribution")
    profit_fig = plot_profit_distribution(trades)
    st.plotly_chart(profit_fig, use_container_width=True)

    st.subheader("🕐 Timing & Volatility Heatmap")
    heatmap_fig = plot_profitability_heatmap(trades)
    st.plotly_chart(heatmap_fig, use_container_width=True)

    st.markdown("---")
    st.subheader("💡 Key Insights")
    if insights:
        for i, insight in enumerate(insights, 1):
            st.write(f"{i}. {insight}")
    else:
        st.info("No specific insights generated at this time.")

    st.markdown("---")
    st.subheader("🧠 Strategy Explanation")
    st.markdown(
        """
        This technical analysis strategy uses two proven indicators to identify market trends and timing:
        """
    )
    st.markdown(strategy_explanation_text())

    if show_strategy:
        st.markdown("---")
        st.subheader("⚙️ Strategy & Pattern Performance")
        st.write("Top symbol-side combinations ranked by realized profit.")
        
        strategy_display = strategy_df.head(15).copy()
        strategy_display["Total_PnL"] = strategy_display["Total_PnL"].apply(lambda x: f"{x:,.2f}")
        strategy_display["Average_PnL"] = strategy_display["Average_PnL"].apply(lambda x: f"{x:,.2f}")
        strategy_display = strategy_display.rename(columns={"Trade_Count": "Trades"})
        
        st.dataframe(strategy_display, use_container_width=True, hide_index=True)

        st.write("**Hourly Performance Edge**")
        hourly_edge = backtester.hourly_edge()
        hourly_display = hourly_edge.copy()
        hourly_display["Total_PnL"] = hourly_display["Total_PnL"].apply(lambda x: f"{x:,.2f}")
        hourly_display["Average_PnL"] = hourly_display["Average_PnL"].apply(lambda x: f"{x:,.2f}")
        st.dataframe(hourly_display, use_container_width=True, hide_index=True)

    if show_backtest:
        st.markdown("---")
        st.subheader("🔍 Backtest Diagnostics")
        st.write("Evaluate directional edge (BUY vs SELL) and symbol-level trade performance.")
        
        st.write("**Directional Edge (BUY vs SELL)**")
        side_edge = backtester.side_edge()
        side_display = side_edge.copy()
        side_display["Total_PnL"] = side_display["Total_PnL"].apply(lambda x: f"{x:,.2f}")
        side_display["Average_PnL"] = side_display["Average_PnL"].apply(lambda x: f"{x:,.2f}")
        st.dataframe(side_display, use_container_width=True, hide_index=True)
        
        st.write("**Symbol Performance (Top 12)**")
        symbol_edge = backtester.symbol_edge().head(12)
        symbol_display = symbol_edge.copy()
        symbol_display["Total_PnL"] = symbol_display["Total_PnL"].apply(lambda x: f"{x:,.2f}")
        symbol_display["Average_PnL"] = symbol_display["Average_PnL"].apply(lambda x: f"{x:,.2f}")
        st.dataframe(symbol_display, use_container_width=True, hide_index=True)

    if show_anomalies and not anomalies_df.empty:
        st.markdown("---")
        st.subheader("⚠️ Anomaly Detection")
        st.write(
            "Trades with unusual characteristics: extreme profits/losses (>3σ) or high fee ratios (>2%). Review for suspicious activity or risk concentration."
        )
        
        anomaly_display = anomalies_df[[
            "time", "symbol", "side", "realizedProfit", "fee", "fee_ratio", "profit_zscore", "Port_IDs"
        ]].head(20).copy()
        
        anomaly_display["realizedProfit"] = anomaly_display["realizedProfit"].apply(lambda x: f"{x:,.2f}")
        anomaly_display["fee"] = anomaly_display["fee"].apply(lambda x: f"{x:,.4f}")
        anomaly_display["fee_ratio"] = anomaly_display["fee_ratio"].apply(lambda x: f"{x:.4f}")
        anomaly_display["profit_zscore"] = anomaly_display["profit_zscore"].apply(lambda x: f"{x:.2f}")
        
        st.dataframe(anomaly_display, use_container_width=True, hide_index=True)

    if not overtrading_df.empty:
        st.markdown("---")
        st.subheader("🚨 Overtrading Alert")
        st.write(
            "Portfolios executing ≥20 trades within a single hour. May indicate risk concentration or excessive position management."
        )
        
        overtrading_display = overtrading_df.head(20).copy()
        overtrading_display = overtrading_display.rename(columns={"Trades_Per_Hour": "Trades/Hour"})
        
        st.dataframe(overtrading_display, use_container_width=True, hide_index=True)

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        "🏆 Built for portfolio-grade trading analytics and production-level reporting.\n\n"
        "**Disclaimer:** Past performance does not guarantee future results. Use for educational and analytical purposes only."
    )


if __name__ == "__main__":
    main()
