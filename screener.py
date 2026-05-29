import os
from datetime import date, timedelta

import pandas as pd
import requests


FMP_API_KEY = os.getenv("FMP_API_KEY")

if not FMP_API_KEY:
    raise RuntimeError("FMP_API_KEY fehlt. Lege ihn als GitHub Secret an.")


START_DATE = date.today()
END_DATE = START_DATE + timedelta(days=7)

MIN_PERFORMANCE_2M = 15.0
DATA_DIR = "data"
OUTPUT_FILE = os.path.join(DATA_DIR, "earnings_momentum_screen.csv")

COLUMNS = [
    "symbol",
    "company",
    "earnings_date",
    "current_close",
    "performance_2m_pct",
    "above_sma_20",
    "above_sma_50",
    "distance_sma_50_pct",
    "score",
    "rating",
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

    if momentum["performance_2m"] > 15:
        score += 30

    if momentum["performance_2m"] > 25:
        score += 10

    if momentum["above_sma_20"]:
        score += 15

    if momentum["above_sma_50"]:
        score += 20

    if momentum["distance_sma_50"] > 10:
        score += 10

    if score >= 80:
        rating = "A"
    elif score >= 65:
        rating = "B"
    elif score >= 50:
        rating = "C"
    else:
        rating = "Avoid"

    return score, rating


def run_screen():
    os.makedirs(DATA_DIR, exist_ok=True)

    earnings = get_earnings_calendar(START_DATE, END_DATE)
    print(f"Earnings gefunden: {len(earnings)}")

    results = []

    for item in earnings:
        symbol = item.get("symbol")
        company = item.get("name")
        earnings_date = item.get("date")

        if not symbol:
            continue

        try:
            prices = get_historical_prices(symbol)
            momentum = calculate_momentum(prices)

            if momentum is None:
                continue

            if momentum["performance_2m"] <= MIN_PERFORMANCE_2M:
                continue

            score, rating = score_stock(momentum)

            results.append(
                {
                    "symbol": symbol,
                    "company": company,
                    "earnings_date": earnings_date,
                    "current_close": round(momentum["current_close"], 2),
                    "performance_2m_pct": round(momentum["performance_2m"], 2),
                    "above_sma_20": momentum["above_sma_20"],
                    "above_sma_50": momentum["above_sma_50"],
                    "distance_sma_50_pct": round(momentum["distance_sma_50"], 2),
                    "score": score,
                    "rating": rating,
                }
            )

            print(f"Treffer: {symbol} {round(momentum['performance_2m'], 2)}%")

        except Exception as error:
            print(f"Fehler bei {symbol}: {error}")

    df = pd.DataFrame(results, columns=COLUMNS)

    if not df.empty:
        df = df.sort_values(
            by=["score", "performance_2m_pct"],
            ascending=[False, False],
        )

    df.to_csv(OUTPUT_FILE, index=False)

    print(f"Treffer insgesamt: {len(df)}")
    print(f"CSV geschrieben nach: {OUTPUT_FILE}")

    return df


if __name__ == "__main__":
    screen = run_screen()
    print(screen)
