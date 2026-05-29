import os
from datetime import date, timedelta

import pandas as pd
import requests
import streamlit as st


def get_fmp_api_key():
    key = os.getenv("FMP_API_KEY")

    if key:
        return key

    try:
        return st.secrets["FMP_API_KEY"]
    except Exception:
        return None


FMP_API_KEY = get_fmp_api_key()

if not FMP_API_KEY:
    raise RuntimeError(
        "FMP_API_KEY fehlt. Lege ihn in GitHub Actions und in Streamlit Secrets an."
    )


DATA_DIR = "data"
FILTERED_FILE = os.path.join(DATA_DIR, "earnings_momentum_screen.csv")
ALL_FILE = os.path.join(DATA_DIR, "earnings_momentum_all.csv")

WKN_MAP = {
    "DELL": "A2N6WP",
    "ADBE": "871981",
    "COST": "888351",
    "DOCU": "A2JHLZ",
}

COLUMNS = [
    "symbol",
    "company",
    "wkn",
    "isin",
    "earnings_date",
    "current_close",
    "performance_2m_pct",
    "above_sma_20",
    "above_sma_50",
    "distance_sma_50_pct",
    "score",
    "rating",
    "status",
    "interpretation",
    "action",
    "chart_url",
]


def get_json(url: str):
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


def get_earnings_calendar(start_date, end_date):
    url = (
        "https://financialmodelingprep.com/stable/earnings-calendar"
        f"?from={start_date}&to={end_date}&apikey={FMP_API_KEY}"
    )
    return get_json(url)


def get_company_profile(symbol):
    url = (
        "https://financialmodelingprep.com/stable/profile"
        f"?symbol={symbol}&apikey={FMP_API_KEY}"
    )

    try:
        data = get_json(url)
    except Exception:
        return {}

    if isinstance(data, list) and data:
        return data[0]

    if isinstance(data, dict):
        return data

    return {}


def get_historical_prices(symbol):
    url = (
        "https://financialmodelingprep.com/stable/historical-price-eod/full"
        f"?symbol={symbol}&apikey={FMP_API_KEY}"
    )

    data = get_json(url)

    if not data:
        return None

    df = pd.DataFrame(data)

    if "date" not in df.columns or "close" not in df.columns:
        return None

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    return df


def calculate_momentum(df):
    if df is None or len(df) < 50:
        return None

    current_close = float(df.iloc[-1]["close"])
    close_42_days_ago = float(df.iloc[-43]["close"])

    if close_42_days_ago <= 0:
        return None

    performance_2m = (current_close / close_42_days_ago - 1) * 100

    sma_20 = df["close"].tail(20).mean()
    sma_50 = df["close"].tail(50).mean()

    if sma_50 <= 0:
        return None

    return {
        "current_close": current_close,
        "performance_2m": performance_2m,
        "sma_20": sma_20,
        "sma_50": sma_50,
        "above_sma_20": current_close > sma_20,
        "above_sma_50": current_close > sma_50,
        "distance_sma_50": (current_close / sma_50 - 1) * 100,
    }


def score_stock(momentum):
    score = 0

    if momentum["performance_2m"] >= 15:
        score += 30
    if momentum["performance_2m"] >= 25:
        score += 10
    if momentum["above_sma_20"]:
        score += 15
    if momentum["above_sma_50"]:
        score += 20
    if momentum["distance_sma_50"] >= 10:
        score += 10

    if score >= 80:
        rating = "A"
    elif score >= 65:
        rating = "B"
    elif score >= 50:
        rating = "C"
    else:
        rating = "Watch"

    return score, rating


def classify_stock(performance, min_performance):
    if performance >= min_performance:
        return (
            "Treffer",
            "Aktie erfüllt den eingestellten Momentum-Filter.",
            "Detailanalyse prüfen",
        )

    if performance >= min_performance - 5:
        return (
            "Knapp darunter",
            "Nahe am Filter, aber noch kein starkes Setup.",
            "Watchlist",
        )

    if performance >= 5:
        return (
            "Unter Filter",
            "Positives Momentum, aber zu schwach für dein Setup.",
            "Nur beobachten",
        )

    if performance >= 0:
        return (
            "Unter Filter",
            "Kaum Momentum. Kein institutioneller Vorlauf erkennbar.",
            "Ignorieren",
        )

    return (
        "Schwach",
        "Negatives Momentum vor Earnings. Für diesen Screener uninteressant.",
        "Ignorieren",
    )


def chart_url(symbol):
    return f"https://www.tradingview.com/chart/?symbol=NASDAQ%3A{symbol}"


def build_result_row(symbol, company, earnings_date, momentum, min_performance):
    profile = get_company_profile(symbol)

    company_name = (
        company
        if company and company != "n/a"
        else profile.get("companyName")
        or profile.get("companyNameLong")
        or profile.get("name")
        or symbol
    )

    isin = profile.get("isin") or profile.get("ISIN") or "n/a"
    wkn = WKN_MAP.get(symbol, "n/a")

    score, rating = score_stock(momentum)
    performance = round(momentum["performance_2m"], 2)
    status, interpretation, action = classify_stock(performance, min_performance)

    return {
        "symbol": symbol,
        "company": company_name,
        "wkn": wkn,
        "isin": isin,
        "earnings_date": earnings_date,
        "current_close": round(momentum["current_close"], 2),
        "performance_2m_pct": performance,
        "above_sma_20": momentum["above_sma_20"],
        "above_sma_50": momentum["above_sma_50"],
        "distance_sma_50_pct": round(momentum["distance_sma_50"], 2),
        "score": score,
        "rating": rating,
        "status": status,
        "interpretation": interpretation,
        "action": action,
        "chart_url": chart_url(symbol),
    }


def analyze_single_symbol(symbol, min_performance_2m=15.0):
    symbol = symbol.strip().upper()

    if not symbol:
        return None

    prices = get_historical_prices(symbol)
    momentum = calculate_momentum(prices)

    if momentum is None:
        return None

    return pd.DataFrame(
        [
            build_result_row(
                symbol=symbol,
                company="",
                earnings_date="nicht geprüft",
                momentum=momentum,
                min_performance=min_performance_2m,
            )
        ],
        columns=COLUMNS,
    )


def run_screen(lookback_days=7, forward_days=14, min_performance_2m=15.0):
    os.makedirs(DATA_DIR, exist_ok=True)

    today = date.today()
    start_date = today - timedelta(days=lookback_days)
    end_date = today + timedelta(days=forward_days)

    earnings = get_earnings_calendar(start_date, end_date)

    all_results = []
    skipped_no_symbol = 0
    skipped_no_prices = 0
    symbols_seen = set()

    for item in earnings:
        symbol = item.get("symbol")
        company = (
            item.get("companyName")
            or item.get("name")
            or item.get("company")
            or "n/a"
        )
        earnings_date = item.get("date")

        if not symbol:
            skipped_no_symbol += 1
            continue

        symbol = symbol.upper().strip()

        if symbol in symbols_seen:
            continue

        symbols_seen.add(symbol)

        try:
            prices = get_historical_prices(symbol)
            momentum = calculate_momentum(prices)

            if momentum is None:
                skipped_no_prices += 1
                continue

            all_results.append(
                build_result_row(
                    symbol=symbol,
                    company=company,
                    earnings_date=earnings_date,
                    momentum=momentum,
                    min_performance=min_performance_2m,
                )
            )

        except Exception as error:
            print(f"Fehler bei {symbol}: {error}")

    all_df = pd.DataFrame(all_results, columns=COLUMNS)

    if not all_df.empty:
        all_df = all_df.sort_values(
            by=["performance_2m_pct", "score"],
            ascending=[False, False],
        )

    filtered_df = all_df[all_df["performance_2m_pct"] >= min_performance_2m].copy()

    all_df.to_csv(ALL_FILE, index=False)
    filtered_df.to_csv(FILTERED_FILE, index=False)

    best_symbol = None
    best_performance = None

    if not all_df.empty:
        best_symbol = all_df.iloc[0]["symbol"]
        best_performance = all_df.iloc[0]["performance_2m_pct"]

    stats = {
        "earnings_found": len(earnings),
        "stocks_with_price_data": len(all_df),
        "hits": len(filtered_df),
        "skipped_no_symbol": skipped_no_symbol,
        "skipped_no_prices": skipped_no_prices,
        "start_date": str(start_date),
        "end_date": str(end_date),
        "min_performance_2m": min_performance_2m,
        "best_symbol": best_symbol,
        "best_performance": best_performance,
    }

    return filtered_df, all_df, stats


if __name__ == "__main__":
    filtered, all_candidates, stats = run_screen()
    print(stats)
    print(filtered)
