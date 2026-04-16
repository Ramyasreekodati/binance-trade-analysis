from pathlib import Path

import pandas as pd
import streamlit as st

from scripts.backtest import StrategyBacktester
from scripts.data import clean_trade_data, load_trade_data, validation_report
from scripts.insights import generate_insights
from scripts.metrics import (
    build_strategy_performance,
    build_time_analytics,
    detect_anomalies,
    detect_overtrading,
    summarize_portfolios,
)
from scripts.visualization import (
    plot_drawdown_curve,
    plot_equity_curve,
    plot_profit_distribution,
    plot_profitability_heatmap,
)

DEFAULT_SOURCE = Path("TRADES_CopyTr_90D_ROI.csv")


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
        return load_trade_data(DEFAULT_SOURCE)

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
        st.stop()

    trades = clean_trade_data(raw_df)
    validation = validation_report(trades)
    metrics_df = summarize_portfolios(trades)
    time_analytics = build_time_analytics(trades)
    strategy_df = build_strategy_performance(trades)
    anomalies_df = detect_anomalies(trades)
    overtrading_df = detect_overtrading(trades)
    insights = generate_insights(trades, metrics_df)
    backtester = StrategyBacktester(trades)

    selected_portfolio = st.sidebar.selectbox(
        "Select portfolio", format_portfolio_selector(metrics_df)
    )
    show_anomalies = st.sidebar.checkbox("Show anomaly trade table", value=True)
    show_strategy = st.sidebar.checkbox("Show strategy evaluation", value=True)
    show_backtest = st.sidebar.checkbox("Show backtest diagnostics", value=True)

    filtered_portfolio = None
    if selected_portfolio != "All portfolios":
        filtered_portfolio = int(selected_portfolio)

    st.header("Portfolio Summary")
    total_profit = float(trades["realizedProfit"].sum())
    average_sharpe = float(metrics_df["Sharpe_Ratio"].mean())
    average_win_rate = float(metrics_df["Win_Rate"].mean())
    average_drawdown = float(metrics_df["Max_Drawdown"].mean())

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Net Realized PnL", f"{total_profit:,.2f} USDT")
    col2.metric("Average Sharpe Ratio", f"{average_sharpe:.2f}")
    col3.metric("Average Win Rate", f"{average_win_rate:.1f}%")
    col4.metric("Average Max Drawdown", f"{average_drawdown:,.2f} USDT")

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
