


import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.data import clean_trade_data, load_trade_data, validation_report
from scripts.insights import generate_insights
from scripts.metrics import (
    build_strategy_performance,
    detect_anomalies,
    detect_overtrading,
    summarize_portfolios,
)

RAW_FILE = ROOT / "TRADES_CopyTr_90D_ROI.csv"
OUTPUT_DIR = ROOT / "outputs"


def run_pipeline(raw_path: Path) -> None:
    print("Loading raw trade data...")
    raw_df = load_trade_data(raw_path)

    print("Cleaning and normalizing trade records...")
    trades = clean_trade_data(raw_df)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    parsed_path = OUTPUT_DIR / "parsed_trades.csv"
    trades.to_csv(parsed_path, index=False)
    print(f"Saved clean trade data to {parsed_path}")

    print("Generating portfolio metrics...")
    portfolio_metrics = summarize_portfolios(trades)
    metrics_path = OUTPUT_DIR / "portfolio_metrics.csv"
    portfolio_metrics.to_csv(metrics_path, index=False)
    print(f"Saved portfolio metrics to {metrics_path}")

    print("Analyzing strategy performance and risk events...")
    strategy_metrics = build_strategy_performance(trades)
    strategy_path = OUTPUT_DIR / "strategy_performance.csv"
    strategy_metrics.to_csv(strategy_path, index=False)

    anomalies = detect_anomalies(trades)
    anomalies_path = OUTPUT_DIR / "anomaly_trades.csv"
    anomalies.to_csv(anomalies_path, index=False)

    overtrading_events = detect_overtrading(trades)
    overtrading_path = OUTPUT_DIR / "overtrading_events.csv"
    overtrading_events.to_csv(overtrading_path, index=False)

    top20_path = OUTPUT_DIR / "top_20_portfolios.csv"
    portfolio_metrics.sort_values("Total_PnL", ascending=False).head(20).to_csv(top20_path, index=False)

    insights = generate_insights(trades, portfolio_metrics)
    insights_path = OUTPUT_DIR / "generated_insights.txt"
    with insights_path.open("w", encoding="utf-8") as handle:
        handle.write("\n".join(insights))

    validation = validation_report(trades)
    validation_path = OUTPUT_DIR / "validation_report.txt"
    with validation_path.open("w", encoding="utf-8") as handle:
        for key, value in validation.items():
            handle.write(f"{key}: {value}\n")

    print(f"Saved strategy metrics to {strategy_path}")
    print(f"Saved anomaly report to {anomalies_path}")
    print(f"Saved overtrading report to {overtrading_path}")
    print(f"Saved top 20 portfolio ranking to {top20_path}")
    print(f"Saved insights to {insights_path}")
    print(f"Saved validation summary to {validation_path}")
    print("Pipeline completed successfully.")


def main() -> None:
    run_pipeline(RAW_FILE)


if __name__ == "__main__":
    main()
