"""Build the comparison dataset, metrics, and five report figures.

Run: .venv/bin/python src/analyze.py
Stocks: pinned KRX-origin marcap Close; index: published NAVER KOSPI Close.
Preparation observations support rolling statistics but not period returns.
"""

import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.ticker import FuncFormatter
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
KEYS = ["samsung", "sk_hynix", "kospi"]
NAMES = {"samsung": "삼성전자", "sk_hynix": "SK하이닉스", "kospi": "코스피"}
COLORS = {"samsung": "#1455FF", "sk_hynix": "#F21D35", "kospi": "#00A846"}
LINES = {"samsung": "-", "sk_hynix": "--", "kospi": ":"}


def load_prices():
    manifest = json.loads((ROOT / "data/manifest.json").read_text(encoding="utf-8"))
    comparison = json.loads((ROOT / "results/krx_comparison.json").read_text(encoding="utf-8"))
    source_check = json.loads((ROOT / "results/source_verification.json").read_text(encoding="utf-8"))
    for item in comparison["series"]:
        if item["naver_only_dates"] or item["krx_only_dates"]:
            raise ValueError("KRX/NAVER date coverage differs")
    for item in source_check["series"]:
        if item["missing_vs_calendar"] or item["extra_vs_calendar"]:
            raise ValueError("Trading calendar reconciliation is incomplete")
    index_check = next(item for item in source_check["series"] if item["key"] == "kospi")
    if index_check["price_mismatches"] or index_check["naver_only_dates"] or index_check["yahoo_only_dates"]:
        raise ValueError("KOSPI provider comparison requires investigation")
    records = json.loads((ROOT / "data/reference/krx_selected_close.json").read_text(encoding="utf-8"))
    stocks = pd.DataFrame(records)
    stocks["Code"] = stocks["Code"].astype(str).str.zfill(6)
    if stocks.duplicated(["Date", "Code"]).any():
        raise ValueError("Duplicate KRX stock observations")
    prices = stocks.pivot(index="Date", columns="Code", values="Close").rename(columns={"005930": "samsung", "000660": "sk_hynix"})
    index = pd.read_csv(ROOT / "data/raw/kospi_daily.csv", encoding="utf-8-sig").set_index("Date")["Close"]
    prices = prices.join(index.rename("kospi"), how="outer")[KEYS].sort_index()
    prices.index = pd.to_datetime(prices.index)
    prices.index.name = "Date"
    prices = prices.astype(float)
    if prices.isna().any().any() or not np.isfinite(prices.to_numpy()).all() or (prices <= 0).any().any():
        raise ValueError("Invalid price value in analysis dataset")
    expected = pd.to_datetime(json.loads((ROOT / "data/reference/xkrx_sessions.json").read_text())["sessions"])
    if not prices.index.equals(pd.DatetimeIndex(expected, name="Date")):
        raise ValueError("Analysis dataset does not match the reconciled calendar")
    selected = prices.loc[manifest["analysis_start"]:manifest["analysis_end"]]
    if len(selected) < 100:
        raise ValueError("Fewer than 100 observations")
    (ROOT / "data/processed").mkdir(exist_ok=True)
    prices.to_csv(ROOT / "data/processed/close_prices.csv", encoding="utf-8-sig", date_format="%Y-%m-%d")
    selected.to_csv(ROOT / "data/processed/analysis_prices.csv", encoding="utf-8-sig", date_format="%Y-%m-%d")
    # Record changed closes while preserving all original NAVER files.
    with (ROOT / "results/source_differences.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["series", "Date", "naver_close", "krx_close"])
        writer.writeheader()
        for series in comparison["series"]:
            writer.writerows({"series": series["key"], **row} for row in series["naver_krx_mismatches"])
    return prices, selected, manifest, comparison


def configure_plot():
    fonts = {font.name for font in font_manager.fontManager.ttflist}
    family = next((name for name in ["AppleGothic", "Malgun Gothic", "NanumGothic", "Nanum Gothic", "Noto Sans CJK KR"] if name in fonts), "DejaVu Sans")
    plt.rcParams.update({"font.family": family, "font.size": 12, "axes.unicode_minus": False,
                         "figure.facecolor": "white", "axes.facecolor": "white",
                         "axes.spines.top": False, "axes.spines.right": False,
                         "axes.edgecolor": "#CBD5E1", "axes.labelcolor": "#334155",
                         "text.color": "#172033", "xtick.color": "#475569", "ytick.color": "#475569",
                         "xtick.major.size": 0, "ytick.major.size": 0,
                         "xtick.major.pad": 9, "ytick.major.pad": 8,
                         "axes.titleweight": "normal", "axes.axisbelow": True,
                         "legend.fontsize": 11, "legend.handlelength": 2.5,
                         "savefig.dpi": 180})


def heading(fig, title, subtitle):
    fig.suptitle(title, x=0.075, ha="left", fontsize=21, y=0.97)
    fig.text(0.075, 0.905, subtitle, ha="left", fontsize=11, color="#64748B")
    fig.text(0.075, 0.025, "2023.01.02—2026.09.30 · 배당 미포함 · 기업: KRX 원천 종가 / 코스피: NAVER", fontsize=9, color="#64748B")


def legend(ax, **kwargs):
    return ax.legend(frameon=False, loc="upper left", ncol=3, **kwargs)


def format_time(ax):
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 7]))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y.%m"))
    ax.grid(axis="y", color="#E5EAF0", linewidth=0.7)
    ax.margins(x=0.015)
    ax.set_xlabel("날짜")


def save(fig, name):
    fig.savefig(ROOT / "images" / name, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def make_figures(prices, selected, returns, monthly, indexed, drawdown, totals):
    configure_plot()
    (ROOT / "images").mkdir(exist_ok=True)
    fig, ax = plt.subplots(figsize=(13, 7.2))
    fig.subplots_adjust(left=0.085, right=0.97, top=0.82, bottom=0.15)
    heading(fig, "같은 출발선에서, 누가 더 많이 올랐을까?", "처음 값을 모두 100으로 맞춰 비교 · 200이면 시작 가격의 2배")
    for key in KEYS:
        ax.plot(indexed.index, indexed[key], color=COLORS[key], linestyle=LINES[key], linewidth=2.3,
                label=NAMES[key])
        endpoint = indexed[key].iloc[-1]
        ax.scatter(indexed.index[-1], endpoint, color=COLORS[key], s=30, zorder=4)
        offset = 12 if key == "samsung" else -12 if key == "kospi" else 0
        ax.annotate(f"+{totals[key]:,.1f}%", (indexed.index[-1], endpoint),
                    xytext=(9, offset), textcoords="offset points", va="center", fontsize=12,
                    color=COLORS[key])
    ax.axhline(100, color="#94A3B8", linewidth=0.8)
    ax.set_ylabel("시작 가격을 100으로 맞춘 값")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:,.0f}"))
    format_time(ax)
    ax.set_xlim(indexed.index[0], indexed.index[-1] + pd.Timedelta(days=210))
    ax.set_xticks(pd.date_range("2023-01-01", "2026-07-01", freq="6MS"))
    ax.set_ylim(bottom=0)
    legend(ax, bbox_to_anchor=(0, 1.10), borderaxespad=0)
    save(fig, "01_relative_performance.png")

    fig, axes = plt.subplots(2, 1, figsize=(13, 9.6), sharex=True)
    fig.subplots_adjust(left=0.10, right=0.97, top=0.82, bottom=0.11, hspace=0.36)
    heading(fig, "하루의 출렁임을 줄이면, 큰 흐름이 보여요", "종가와 최근 20·60거래일 평균 비교 · 평균 기간이 길수록 부드럽고 느리게 반응")
    for ax, key in zip(axes, KEYS[:2]):
        ax.plot(selected.index, selected[key], color=COLORS[key], linewidth=1.6, label="실제 종가")
        for window, color, style in [(20, "#475569", "--"), (60, "#8B5CF6", "-")]:
            ax.plot(selected.index, prices[key].rolling(window).mean().reindex(selected.index), color=color, linestyle=style,
                    linewidth=1.7, label=f"{window}거래일 평균")
        ax.set_title(NAMES[key], loc="left", fontsize=15, color=COLORS[key], pad=10)
        ax.set_ylabel("가격 (원)")
        ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:,.0f}"))
        format_time(ax)
        legend(ax)
    axes[0].set_xlabel("")
    save(fig, "02_moving_averages.png")

    fig, axes = plt.subplots(2, 2, figsize=(14, 9.8), sharey=True)
    fig.subplots_adjust(left=0.075, right=0.98, top=0.79, bottom=0.12, wspace=0.09, hspace=0.36)
    heading(fig, "한 달씩 나눠 보면, 언제 차이가 났을까?", "직전 달 말 대비 가격 변화율 · 0선 위는 상승, 아래는 하락 · 네 패널의 세로 눈금은 동일")
    low = np.floor(monthly.min().min() * 100 / 10) * 10 - 10
    high = np.ceil(monthly.max().max() * 100 / 10) * 10 + 5
    for ax, year in zip(axes.flat, range(2023, 2027)):
        part = monthly.loc[str(year)]
        x = part.index.month.to_numpy() - 1
        for i, key in enumerate(KEYS):
            ax.bar(x + (i - 1) * 0.26, part[key] * 100, width=0.24, color=COLORS[key], label=NAMES[key], zorder=3)
        ax.axhline(0, color="#64748B", linewidth=1)
        ax.set_xlim(-0.65, 11.65)
        ax.set_ylim(low, high)
        ax.set_xticks(x, [f"{month}월" for month in part.index.month], fontsize=10)
        ax.set_title(f"{year}년" + (" · 1~9월" if year == 2026 else ""), loc="left", fontsize=15, pad=12)
        ax.grid(axis="y", color="#E5EAF0", linewidth=0.7)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper left", bbox_to_anchor=(0.07, 0.88), frameon=False, ncol=3)
    axes[0, 0].set_ylabel("월별 수익률 (%)")
    axes[1, 0].set_ylabel("월별 수익률 (%)")
    axes[1, 0].set_xlabel("월")
    axes[1, 1].set_xlabel("월")
    save(fig, "03_monthly_returns.png")

    volatility = returns.rolling(20).std(ddof=1).reindex(selected.index) * 100
    fig, ax = plt.subplots(figsize=(13, 7.2))
    fig.subplots_adjust(left=0.085, right=0.97, top=0.82, bottom=0.15)
    heading(fig, "언제 더 크게 흔들렸을까?", "선이 높을수록 하루하루 변화가 들쭉날쭉 · 최근 20거래일 기준 · 연환산하지 않음")
    for key in KEYS:
        ax.plot(volatility.index, volatility[key], color=COLORS[key], linestyle=LINES[key], linewidth=2, label=NAMES[key])
    ax.set_ylabel("일별 수익률 표준편차 (%)")
    format_time(ax)
    legend(ax, bbox_to_anchor=(0, 1.10), borderaxespad=0)
    ax.set_ylim(bottom=0)
    save(fig, "04_rolling_volatility.png")

    fig, ax = plt.subplots(figsize=(13, 7.2))
    fig.subplots_adjust(left=0.085, right=0.97, top=0.82, bottom=0.15)
    heading(fig, "이전 최고 가격에서, 얼마나 떨어졌을까?", "0%는 그때까지의 최고 가격 · 아래로 깊게 내려갈수록 고점 대비 하락 폭이 큼")
    for key in KEYS:
        values = drawdown[key] * 100
        ax.plot(drawdown.index, values, color=COLORS[key], linestyle=LINES[key], linewidth=2, label=NAMES[key])
        trough = values.idxmin()
        ax.scatter(trough, values.min(), color=COLORS[key], s=35, zorder=5)
        ax.annotate(f"최대 낙폭 {values.min():.1f}%", (trough, values.min()),
                    xytext=(-12, -20 if key == "sk_hynix" else 14), textcoords="offset points",
                    ha="right", fontsize=11, color=COLORS[key])
    ax.axhline(0, color="#A8B0B8", linewidth=0.8)
    ax.set_ylabel("고점 대비 낙폭 (%)")
    format_time(ax)
    ax.set_ylim(min(drawdown.min()) * 100 - 9, 5)
    legend(ax, bbox_to_anchor=(0, 1.10), borderaxespad=0)
    save(fig, "05_drawdown.png")


def main():
    prices, selected, manifest, comparison = load_prices()
    returns = prices.pct_change(fill_method=None)
    indexed = selected.div(selected.iloc[0]) * 100
    totals = (selected.iloc[-1].div(selected.iloc[0]) - 1) * 100
    monthly = prices.resample("ME").last().pct_change(fill_method=None).loc[manifest["analysis_start"]:manifest["analysis_end"]]
    drawdown = selected.div(selected.cummax()) - 1
    metrics = []
    annual = []
    for key in KEYS:
        trough = drawdown[key].idxmin()
        peak = selected.loc[:trough, key].idxmax()
        metrics.append({
            "series": key, "name": NAMES[key], "first_close": float(selected[key].iloc[0]),
            "last_close": float(selected[key].iloc[-1]), "price_return_pct": float(totals[key]),
            "last_indexed_value": float(indexed[key].iloc[-1]),
            "max_drawdown_pct": float(drawdown[key].min() * 100),
            "drawdown_peak_date": peak.strftime("%Y-%m-%d"), "drawdown_trough_date": trough.strftime("%Y-%m-%d"),
            "annualized_daily_volatility_pct": float(returns.loc[selected.index, key].std(ddof=1) * np.sqrt(252) * 100),
        })
        for year in range(2023, 2027):
            period = selected.loc[str(year), key]
            baseline = prices.loc[prices.index < period.index[0], key].iloc[-1]
            annual.append({"series": key, "year": year, "period": str(year) if year < 2026 else "2026-01~09",
                           "baseline_close": float(baseline), "last_close": float(period.iloc[-1]),
                           "price_return_pct": float((period.iloc[-1] / baseline - 1) * 100)})
    result = {"analysis_start": selected.index[0].strftime("%Y-%m-%d"),
              "analysis_end": selected.index[-1].strftime("%Y-%m-%d"), "analysis_rows": len(selected),
              "preparation_rows": len(prices) - len(selected), "stock_source_commit": comparison["commit"],
              "price_basis": "KRX-origin Close for stocks; NAVER KOSPI Close. No dividend reinvestment.",
              "period_return_baseline": "First analysis trading day close (2023-01-02)",
              "annual_return_baseline": "Previous year's final trading day close; 2026 ends September 30",
              "daily_return_basis": "Each trading day's close versus the previous trading day's close; preparation data included for January 2",
              "metrics": metrics, "annual_returns": annual}
    (ROOT / "results/analysis_metrics.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    pd.DataFrame(metrics).to_csv(ROOT / "results/summary_metrics.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(annual).to_csv(ROOT / "results/annual_returns.csv", index=False, encoding="utf-8-sig")
    indexed.to_csv(ROOT / "results/indexed_prices.csv", encoding="utf-8-sig", date_format="%Y-%m-%d")
    monthly.to_csv(ROOT / "results/monthly_returns.csv", encoding="utf-8-sig", date_format="%Y-%m-%d")
    make_figures(prices, selected, returns, monthly, indexed, drawdown, totals)
    for row in metrics:
        print(f"{row['name']}: {row['first_close']:,.2f} → {row['last_close']:,.2f}, 가격 수익률 {row['price_return_pct']:,.2f}%, 최대 낙폭 {row['max_drawdown_pct']:.2f}%")
    print(f"Saved five figures; analysis {len(selected)} observations; {len(monthly)} monthly returns.")


if __name__ == "__main__":
    main()
