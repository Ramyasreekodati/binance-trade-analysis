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
    """Load the default dataset silently for presentation."""
    if DEFAULT_SOURCE.exists():
        return load_default_dataset()
    return pd.DataFrame()


@st.cache_data(show_spinner=True)
def get_clean_data(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Cached wrapper for trade data cleaning."""
    return clean_trade_data(raw_df)


@st.cache_data(show_spinner=False)
def get_analytics(trades: pd.DataFrame, initial_capital: float):
    """Cached wrapper for heavy architectural metrics."""
    metrics_df = summarize_portfolios(trades, initial_capital)
    symbol_performance = summarize_symbol_performance(trades, initial_capital)
    time_analytics = build_time_analytics(trades)
    strategy_df = build_strategy_performance(trades)
    anomalies_df = detect_anomalies(trades)
    overtrading_df = detect_overtrading(trades)
    insights = generate_insights(trades, metrics_df)
    backtester = StrategyBacktester(trades)
    validation = validation_report(trades)
    return (
        metrics_df, 
        symbol_performance, 
        time_analytics, 
        strategy_df, 
        anomalies_df, 
        overtrading_df, 
        insights, 
        backtester,
        validation
    )


def format_portfolio_selector(metrics_df: pd.DataFrame) -> list[str]:
    values = ["All portfolios"]
    values.extend(metrics_df["Port_IDs"].astype(str).tolist())
    return values


def main() -> None:
    st.set_page_config(page_title="Binance Trade Analytics", page_icon="📈", layout="wide")
    
    # --- Sidebar Redesign ---
    st.sidebar.title("📈 BINANCE ANALYTICS")
    st.sidebar.markdown(
        """
        **A Portfolio-Grade Risk Intelligence System**
        
        Transforming raw trade data into institutional-quality insights for risk management and strategy validation.
        """
    )
    
    st.sidebar.markdown("---")

    raw_df = load_data()
    if raw_df.empty:
        st.warning("No trade data available. Upload a valid Binance trade CSV or add the default dataset file.")
        st.stop()

    with st.spinner("Processing deep trade history..."):
        trades = get_clean_data(raw_df)
        
    st.sidebar.subheader("🛠️ Global Controls")
    
    initial_capital = st.sidebar.number_input(
        "Initial Capital (USDT)",
        value=100000.0,
        min_value=1.0,
        step=10000.0,
        help="Starting capital for ROI calculation."
    )
    
    # Calculate metrics after getting initial_capital (cached)
    (
        metrics_df, 
        symbol_performance, 
        time_analytics, 
        strategy_df, 
        anomalies_df, 
        overtrading_df, 
        insights, 
        backtester,
        validation
    ) = get_analytics(trades, initial_capital)

    selected_portfolio = st.sidebar.selectbox(
        "Select Portfolio", format_portfolio_selector(metrics_df)
    )
    selected_timeframe_label = st.sidebar.selectbox(
        "Select Timeframe", ["5m", "1h", "1d"], index=1
    )
    selected_symbol = st.sidebar.selectbox(
        "Analysis Symbol", ["All symbols"] + sorted(trades["symbol"].unique().astype(str).tolist()))
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("👁️ Display Settings")
    show_anomalies = st.sidebar.toggle("Show Anomalies", value=True)
    show_strategy = st.sidebar.toggle("Show Strategy Analysis", value=True)
    show_backtest = st.sidebar.toggle("Show Signal Backtest", value=True)
    
    st.sidebar.markdown("---")
    with st.sidebar.expander("🧠 Strategy Logic", expanded=False):
        st.markdown(
            """
            **EMA Crossover**
            - **Buy:** 12 EMA > 26 EMA
            - **Sell:** 12 EMA < 26 EMA
            
            **RSI Filter**
            - Avoid overbought (>70)
            - Avoid oversold (<30)
            """
        )

    with st.sidebar.expander("📊 Metrics Glossary", expanded=False):
        st.markdown(
            """
            **ROI:** Net Return on Investment relative to starting capital.
            
            **Win Rate:** Percentage of profitable trades.
            
            **Max Drawdown:** Peak-to-trough decline (risk measure).
            """
        )

    st.sidebar.markdown("---")
    st.sidebar.subheader("📋 Analysis Report")
    st.sidebar.info(
        "**Objective:** Evaluate risk-adjusted returns and strategy consistency.\n\n"
        "**Insights:** PnL is highly concentrated in top 3 symbols; volatility peaks during NYC sessions.\n\n"
        "**Observation:** Strategy performs best on 1H timeframe."
    )

    st.sidebar.markdown("---")
    st.sidebar.subheader("💻 Tech Stack")
    st.sidebar.caption("Python • Pandas • Plotly • Streamlit • SciPy")

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

    # --- Main Content Tabs ---
    tab1, tab2 = st.tabs(["📊 Analytics Dashboard", "📖 Project Report"])

    with tab2:
        st.title("🌟 The Trading Story: A Beginner's Guide")
        st.markdown(
            """
            *Welcome! If you are new to the world of crypto and trading, this page is for you. We've built this project to make complex data look simple and understandable.*
            """
        )

        st.markdown("---")
        
        # Section 1: The Big Picture
        st.header("1️⃣ What is this project about?")
        st.write(
            "Imagine you go to a market (like Binance) and buy/sell fruits (like Bitcoin). After 3 months, you have a huge pile of receipts but don't know if you actually made a profit. "
            "This project is like a **Smart Accountant**. It reads all those receipts, organizes them, and tells you: "
            "'Hey, you made $500 profit, and your favorite fruit was Bitcoin!'"
        )

        # Section 2: Understanding Binance
        st.header("2️⃣ What is Binance Trade?")
        st.info(
            "**Binance** is like a giant global digital bank where people trade 'Cryptocurrencies' (Digital Money). \n\n"
            "When you 'Trade', you are either **buying low** to sell high, or predicting the market direction. "
            "Our app looks at your **History**—the actual record of every buy and sell you ever did—to see how well you performed."
        )

        # Section 3: The Secret Language (Metrics)
        st.header("3️⃣ Tools for the Expert Trader")
        st.write("We use three main 'checkpoints' to see if your trading is healthy:")
        
        m_col1, m_col2, m_col3 = st.columns(3)
        with m_col1:
            st.subheader("💰 ROI")
            st.caption("Return on Investment")
            st.write("This is the '% profit' you made. "
                     "If you start with $100 and end with $110, your ROI is 10%. Easy!")
        with m_col2:
            st.subheader("📉 Drawdown")
            st.caption("The 'Deep Dip'")
            st.write("This shows the biggest drop your account had. "
                     "Lower is better! It tells us if your journey was a roller-coaster or a smooth ride.")
        with m_col3:
            st.subheader("🛡️ RSI & EMA")
            st.caption("The Strategy Brain")
            st.write("These are math formulas that try to guess the trend. "
                     "They help us spot if a coin is 'Too Hot' (Overbought) or 'Too Cold' (Oversold).")

        # Section 4: How to use this Dashboard
        st.header("4️⃣ How to explore your data")
        st.markdown(
            """
            1.  **The Sidebar (Left):** Use this to pick your portfolio or a specific coin (like SOL). You can also change your starting capital!
            2.  **Top Metrics:** Look at your **Net PnL**—this is your actual cash profit.
            3.  **Equity Curve (The Line Chart):** This is the most important chart. If the line is going **Up and Right**, you are winning!
            4.  **Decision Intelligence:** This section shows if our 'Virtual Assistant' thinks the current market is a Buy, Sell, or Hold.
            """
        )

        # Section 5: The Science Behind the Scenes
        st.header("5️⃣ How it works (The Pipeline)")
        st.markdown(
            """
            <div style="background-color: #e6f3ff; padding: 15px; border-radius: 8px;">
                <b>Step 1: Reading Data</b> - We load the messy Binance file.<br>
                <b>Step 2: Cleaning</b> - We remove any broken or duplicate records.<br>
                <b>Step 3: Calculating</b> - Our math engine calculates your ROI and Win Rates.<br>
                <b>Step 4: AI Insights</b> - We look for 'Anomalies' (unusual trades) to keep you safe.<br>
                <b>Step 5: Visualization</b> - We draw the pretty charts you see in the other tab!
            </div>
            """, 
            unsafe_allow_html=True
        )

        st.markdown("---")
        st.info("💡 **Pro Tip:** Look at the 'Anomaly Detection' section in the Analytics tab. It flags trades where you paid too much in fees or had an unusually large loss!")

        st.caption("⚠️ **Educational Note:** This dashboard is for learning. Trading is risky, so always be careful with your digital assets!")

    with tab1:
        st.header("📊 Performance Dashboard")
        st.write(f"Analytics based on **{initial_capital:,.0f} USDT** initial capital.")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Net Realized PnL",
                f"{portfolio_metrics['Total_PnL']:,.2f} USDT",
                help="Net profit or loss from all closed trades after fees."
            )

        with col2:
            st.metric(
                "ROI %",
                f"{portfolio_metrics['ROI']:.2f}%",
                help=f"Return on Investment: (Total PnL / {initial_capital:,.0f}) * 100"
            )

        with col3:
            st.metric(
                "Win Rate",
                f"{portfolio_metrics['Win_Rate']:.1f}%",
                help="The percentage of closed trades that resulted in a profit."
            )

        with col4:
            st.metric(
                "Total Trades",
                f"{portfolio_metrics['Total_Trades']:,}",
                help="Total execution count across all symbols and portfolios."
            )

        st.markdown("### 🧭 Decision Intelligence")

        insight_col1, insight_col2, insight_col3, insight_col4 = st.columns([1, 1, 1, 2])

        with insight_col1:
            st.metric("Signal", market_insight["signal"], help="Generated based on EMA crossover and RSI filter.")
        with insight_col2:
            st.metric("Trend", market_insight["trend"], help="Market direction identified by the 12/26 EMA relationship.")
        with insight_col3:
            st.metric("RSI", market_insight["rsi"], help="Momentum indicator. >70 is overbought, <30 is oversold.")
        with insight_col4:
            st.metric("Action", market_insight["action"], help="Specific trading action recommended for current conditions.")

        st.info(f"💡 **Analysis Summary:** {market_insight['reason']}")

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
        st.subheader("🎯 Backtest Diagnostics")
        st.write("Simulated performance based on technical signals from historical data.")

        backtest_col1, backtest_col2, backtest_col3 = st.columns(3)

        with backtest_col1:
            st.metric(
                "Strategy Returns",
                f"{backtest_summary['Cumulative_Return']:.2f}%",
                help="Cumulative profit/loss if following all Buy/Sell signals."
            )

        with backtest_col2:
            st.metric(
                "Max Backtest Drawdown",
                f"{backtest_summary['Max_Drawdown']:.2f}%",
                help="Maximum drop from peak equity during the backtest."
            )

        with backtest_col3:
            st.metric(
                "Signal Count",
                f"{int(backtest_summary['Signals']):,}",
                help="Total number of trading signals generated in this timeframe."
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

        st.markdown("### 💡 Strategic Insights")
        if insights:
            for i, insight in enumerate(insights, 1):
                st.info(f"**Insight {i}:** {insight}")
        else:
            st.info("No specific insights generated for current selection.")

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
