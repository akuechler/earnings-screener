import os
from datetime import date, timedelta
from io import StringIO

import pandas as pd
import requests
import streamlit as st


def get_secret(name):
    value = os.getenv(name)

    if value:
        return value

    try:
        return st.secrets[name]
    except Exception:
        return None


FMP_API_KEY = get_secret("FMP_API_KEY")
FINNHUB_API_KEY = get_secret("FINNHUB_API_KEY")

if not FMP_API_KEY:
    raise RuntimeError(
        "FMP_API_KEY fehlt. Lege ihn in GitHub Actions und in Streamlit Secrets an."
    )

if not FINNHUB_API_KEY:
    raise RuntimeError(
        "FINNHUB_API_KEY fehlt. Lege ihn in GitHub Actions und in Streamlit Secrets an."
    )


DATA_DIR = "data"
FILTERED_FILE = os.path.join(DATA_DIR, "earnings_momentum_screen.csv")
ALL_FILE = os.path.join(DATA_DIR, "earnings_momentum_all.csv")

WKN_MAP = {
    "DELL": "A2N6WP",
    "ADBE": "871981",
    "COST": "888351",
    "DOCU": "A2JHLZ",
    "NVDA": "918422",
    "MSFT": "870747",
    "AAPL": "865985",
    "AMZN": "906866",
    "GOOGL": "A14Y6F",
    "GOOG": "A14Y6H",
    "META": "A1JWVX",
    "TSLA": "A1CX3T",
    "AMD": "863186",
    "AVGO": "A2JG9Z",
    "MU": "869020",
    "CRM": "A0B87V",
    "ORCL": "871460",
    "INTC": "855681",
    "NFLX": "552484",
    "QCOM": "883121",
    "IBM": "851399",
    "NOW": "A1JX4P",
    "SNOW": "A2QB38",
    "PANW": "A1JZ0Q",
    "CRWD": "A2PK2R",
    "SHOP": "A14TJP",
    "PLTR": "A2QA4J",
    "SMCI": "A0MKJF",
    "HPE": "A140KD",
    "HPQ": "A142VP",
}

COMPANY_FALLBACK_MAP = {
    "DELL": "Dell Technologies Inc.",
    "ADBE": "Adobe Inc.",
    "COST": "Costco Wholesale Corporation",
    "DOCU": "DocuSign Inc.",
    "NVDA": "NVIDIA Corporation",
    "MSFT": "Microsoft Corporation",
    "AAPL": "Apple Inc.",
    "AMZN": "Amazon.com Inc.",
    "GOOGL": "Alphabet Inc.",
    "GOOG": "Alphabet Inc.",
    "META": "Meta Platforms Inc.",
    "TSLA": "Tesla Inc.",
    "AMD": "Advanced Micro Devices Inc.",
    "AVGO": "Broadcom Inc.",
    "MU": "Micron Technology Inc.",
    "CRM": "Salesforce Inc.",
    "ORCL": "Oracle Corporation",
    "INTC": "Intel Corporation",
    "NFLX": "Netflix Inc.",
    "QCOM": "Qualcomm Inc.",
    "IBM": "International Business Machines Corporation",
    "NOW": "ServiceNow Inc.",
    "SNOW": "Snowflake Inc.",
    "PANW": "Palo Alto Networks Inc.",
    "CRWD": "CrowdStrike Holdings Inc.",
    "SHOP": "Shopify Inc.",
    "PLTR": "Palantir Technologies Inc.",
    "SMCI": "Super Micro Computer Inc.",
    "HPE": "Hewlett Packard Enterprise Company",
    "HPQ": "HP Inc.",
}

EXCHANGE_FALLBACK_MAP = {
    "DELL": "NYSE",
    "ADBE": "NASDAQ",
    "COST": "NASDAQ",
    "DOCU": "NASDAQ",
    "NVDA": "NASDAQ",
    "MSFT": "NASDAQ",
    "AAPL": "NASDAQ",
    "AMZN": "NASDAQ",
    "GOOGL": "NASDAQ",
    "GOOG": "NASDAQ",
    "META": "NASDAQ",
    "TSLA": "NASDAQ",
    "AMD": "NASDAQ",
    "AVGO": "NASDAQ",
    "MU": "NASDAQ",
    "CRM": "NYSE",
    "ORCL": "NYSE",
    "INTC": "NASDAQ",
    "NFLX": "NASDAQ",
    "QCOM": "NASDAQ",
    "IBM": "NYSE",
    "NOW": "NYSE",
    "SNOW": "NYSE",
    "PANW": "NASDAQ",
    "CRWD": "NASDAQ",
    "SHOP": "NYSE",
    "PLTR": "NASDAQ",
    "SMCI": "NASDAQ",
    "HPE": "NYSE",
    "HPQ": "NYSE",
}

COLUMNS = [
    "symbol",
    "company",
    "wkn",
    "isin",
    "exchange",
    "earnings_date",
    "calendar_source",
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
    "data_source",
]


def get_json(url: str):
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


def get_fmp_earnings_calendar(start_date, end_date):
    url = (
        "https://financialmodelingprep.com/stable/earnings-calendar"
        f"?from={start_date}&to={end_date}&apikey={FMP_API_KEY}"
    )

    try:
        data = get_json(url)
    except Exception as error:
        print(f"FMP Earnings Calendar Fehler: {error}")
        return []

    if isinstance(data, list):
        return data

    return []


def get_finnhub_earnings_calendar(start_date, end_date):
    url = (
        "https://finnhub.io/api/v1/calendar/earnings"
        f"?from={start_date}&to={end_date}&token={FINNHUB_API_KEY}"
    )

    try:
        data = get_json(url)
    except Exception as error:
        print(f"Finnhub Earnings Calendar Fehler: {error}")
        return []

    if isinstance(data, dict):
        return data.get("earningsCalendar", []) or []

    return []


def normalize_symbol(symbol):
    if not symbol:
        return ""

    symbol = str(symbol).upper().strip()

    if "." in symbol:
        return symbol.split(".")[0]

    return symbol


def build_candidates_from_calendars(start_date, end_date):
    candidates = {}
    fmp_earnings = get_fmp_earnings_calendar(start_date, end_date)
    finnhub_earnings = get_finnhub_earnings_calendar(start_date, end_date)

    skipped_no_symbol = 0

    for item in fmp_earnings:
        symbol = normalize_symbol(item.get("symbol"))

        if not symbol:
            skipped_no_symbol += 1
            continue

        company = (
            item.get("companyName")
            or item.get("name")
            or item.get("company")
            or COMPANY_FALLBACK_MAP.get(symbol)
            or symbol
        )

        earnings_date = item.get("date") or item.get("fiscalDateEnding") or "n/a"

        candidates[symbol] = {
            "symbol": symbol,
            "company": company,
            "earnings_date": earnings_date,
            "calendar_source": "FMP",
        }

    for item in finnhub_earnings:
        symbol = normalize_symbol(item.get("symbol"))

        if not symbol:
            skipped_no_symbol += 1
            continue

        earnings_date = item.get("date") or "n/a"

        if symbol in candidates:
            old_source = candidates[symbol]["calendar_source"]

            if "Finnhub" not in old_source:
                candidates[symbol]["calendar_source"] = f"{old_source} + Finnhub"

            if candidates[symbol]["earnings_date"] in ["n/a", None, ""]:
                candidates[symbol]["earnings_date"] = earnings_date
        else:
            candidates[symbol] = {
                "symbol": symbol,
                "company": COMPANY_FALLBACK_MAP.get(symbol, symbol),
                "earnings_date": earnings_date,
                "calendar_source": "Finnhub",
            }

    return candidates, fmp_earnings, finnhub_earnings, skipped_no_symbol


def get_company_profile_from_fmp(symbol):
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


def get_company_profile_from_finnhub(symbol):
    url = (
        "https://finnhub.io/api/v1/stock/profile2"
        f"?symbol={symbol}&token={FINNHUB_API_KEY}"
    )

    try:
        data = get_json(url)
    except Exception:
        return {}

    if isinstance(data, dict):
        return data

    return {}


def get_company_profile(symbol):
    fmp_profile = get_company_profile_from_fmp(symbol)

    if fmp_profile:
        return {
            "company": (
                fmp_profile.get("companyName")
                or fmp_profile.get("companyNameLong")
                or fmp_profile.get("name")
                or COMPANY_FALLBACK_MAP.get(symbol)
                or symbol
            ),
            "isin": fmp_profile.get("isin") or fmp_profile.get("ISIN") or "n/a",
            "exchange": (
                fmp_profile.get("exchangeShortName")
                or fmp_profile.get("exchange")
                or EXCHANGE_FALLBACK_MAP.get(symbol)
                or "NASDAQ"
            ),
        }

    finnhub_profile = get_company_profile_from_finnhub(symbol)

    if finnhub_profile:
        return {
            "company": (
                finnhub_profile.get("name")
                or COMPANY_FALLBACK_MAP.get(symbol)
                or symbol
            ),
            "isin": finnhub_profile.get("isin") or "n/a",
            "exchange": (
                finnhub_profile.get("exchange")
                or EXCHANGE_FALLBACK_MAP.get(symbol)
                or "NASDAQ"
            ),
        }

    return {
        "company": COMPANY_FALLBACK_MAP.get(symbol) or symbol,
        "isin": "n/a",
        "exchange": EXCHANGE_FALLBACK_MAP.get(symbol) or "NASDAQ",
    }


def get_historical_prices_from_fmp(symbol):
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
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df = df.dropna(subset=["date", "close"])
    df = df.sort_values("date")

    if df.empty:
        return None

    df["data_source"] = "FMP"
    return df


def get_historical_prices_from_stooq(symbol):
    symbol = symbol.lower().strip()

    url = f"https://stooq.com/q/d/l/?s={symbol}.us&i=d"

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    text = response.text.strip()

    if not text or "No data" in text:
        return None

    df = pd.read_csv(StringIO(text))

    if "Date" not in df.columns or "Close" not in df.columns:
        return None

    df = df.rename(columns={"Date": "date", "Close": "close"})
    df["date"] = pd.to_datetime(df["date"])
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df = df.dropna(subset=["date", "close"])
    df = df.sort_values("date")

    if df.empty:
        return None

    df["data_source"] = "Stooq"
    return df


def get_historical_prices(symbol):
    symbol = normalize_symbol(symbol)

    try:
        df = get_historical_prices_from_fmp(symbol)

        if df is not None and len(df) >= 50:
            return df
    except Exception as error:
        print(f"FMP-Kursdaten fehlgeschlagen bei {symbol}: {error}")

    try:
        df = get_historical_prices_from_stooq(symbol)

        if df is not None and len(df) >= 50:
            return df
    except Exception as error:
        print(f"Stooq-Kursdaten fehlgeschlagen bei {symbol}: {error}")

    return None


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

    data_source = "n/a"

    if "data_source" in df.columns:
        data_source = str(df.iloc[-1]["data_source"])

    return {
        "current_close": current_close,
        "performance_2m": performance_2m,
        "sma_20": sma_20,
        "sma_50": sma_50,
        "above_sma_20": current_close > sma_20,
        "above_sma_50": current_close > sma_50,
        "distance_sma_50": (current_close / sma_50 - 1) * 100,
        "data_source": data_source,
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
            "Aktie erfüllt den eingestellten Momentum-Filter. Das ist ein Kandidat für eine Detailanalyse.",
            "Detailanalyse prüfen",
        )

    if performance >= min_performance - 5:
        return (
            "Knapp darunter",
            "Aktie liegt nahe am Momentum-Filter, aber erfüllt das Setup noch nicht sauber.",
            "Watchlist",
        )

    if performance >= 5:
        return (
            "Unter Filter",
            "Positives Momentum vorhanden, aber zu schwach für dein Earnings-Momentum-Setup.",
            "Nur beobachten",
        )

    if performance >= 0:
        return (
            "Unter Filter",
            "Kaum Momentum. Kein klarer institutioneller Vorlauf vor den Zahlen erkennbar.",
            "Ignorieren",
        )

    return (
        "Schwach",
        "Negatives Momentum vor Earnings. Für diesen Screener uninteressant.",
        "Ignorieren",
    )


def normalize_exchange_for_tradingview(exchange):
    if not exchange:
        return "NASDAQ"

    exchange = str(exchange).upper().strip()

    if "NEW YORK" in exchange:
        return "NYSE"

    if "NASDAQ" in exchange:
        return "NASDAQ"

    if "NYSE" in exchange:
        return "NYSE"

    exchange_map = {
        "NASDAQ": "NASDAQ",
        "NYSE": "NYSE",
        "AMEX": "AMEX",
        "OTC": "OTC",
        "XETRA": "XETR",
        "FRANKFURT": "FWB",
        "FWB": "FWB",
        "LSE": "LSE",
        "TSX": "TSX",
        "EURONEXT": "EURONEXT",
    }

    return exchange_map.get(exchange, "NASDAQ")


def chart_url(symbol, exchange="NASDAQ"):
    symbol = normalize_symbol(symbol)
    tv_exchange = normalize_exchange_for_tradingview(exchange)

    return f"https://www.tradingview.com/chart/?symbol={tv_exchange}%3A{symbol}"


def build_result_row(
    symbol,
    company,
    earnings_date,
    calendar_source,
    momentum,
    min_performance,
):
    symbol = normalize_symbol(symbol)
    profile = get_company_profile(symbol)

    company_name = (
        profile.get("company")
        or COMPANY_FALLBACK_MAP.get(symbol)
        or company
        or symbol
    )

    isin = profile.get("isin") or "n/a"
    wkn = WKN_MAP.get(symbol, "n/a")
    exchange = profile.get("exchange") or EXCHANGE_FALLBACK_MAP.get(symbol) or "NASDAQ"

    score, rating = score_stock(momentum)
    performance = round(momentum["performance_2m"], 2)
    status, interpretation, action = classify_stock(performance, min_performance)

    return {
        "symbol": symbol,
        "company": company_name,
        "wkn": wkn,
        "isin": isin,
        "exchange": exchange,
        "earnings_date": earnings_date,
        "calendar_source": calendar_source,
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
        "chart_url": chart_url(symbol, exchange),
        "data_source": momentum.get("data_source", "n/a"),
    }


def analyze_single_symbol(symbol, min_performance_2m=15.0):
    symbol = normalize_symbol(symbol)

    if not symbol:
        return None

    try:
        prices = get_historical_prices(symbol)
        momentum = calculate_momentum(prices)

        if momentum is None:
            return None

        return pd.DataFrame(
            [
                build_result_row(
                    symbol=symbol,
                    company=COMPANY_FALLBACK_MAP.get(symbol, symbol),
                    earnings_date="nicht geprüft",
                    calendar_source="Manuelle Prüfung",
                    momentum=momentum,
                    min_performance=min_performance_2m,
                )
            ],
            columns=COLUMNS,
        )

    except Exception as error:
        print(f"Manuelle Prüfung fehlgeschlagen bei {symbol}: {error}")
        return None


def run_screen(
    lookback_days=7,
    forward_days=14,
    min_performance_2m=15.0,
):
    os.makedirs(DATA_DIR, exist_ok=True)

    today = date.today()
    start_date = today - timedelta(days=lookback_days)
    end_date = today + timedelta(days=forward_days)

    candidates, fmp_earnings, finnhub_earnings, skipped_no_symbol = (
        build_candidates_from_calendars(start_date, end_date)
    )

    all_results = []
    skipped_no_prices = 0

    for symbol, candidate in candidates.items():
        try:
            prices = get_historical_prices(symbol)
            momentum = calculate_momentum(prices)

            if momentum is None:
                skipped_no_prices += 1
                continue

            all_results.append(
                build_result_row(
                    symbol=symbol,
                    company=candidate["company"],
                    earnings_date=candidate["earnings_date"],
                    calendar_source=candidate["calendar_source"],
                    momentum=momentum,
                    min_performance=min_performance_2m,
                )
            )

        except Exception as error:
            skipped_no_prices += 1
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
    best_company = None
    best_performance = None

    if not all_df.empty:
        best_symbol = all_df.iloc[0]["symbol"]
        best_company = all_df.iloc[0]["company"]
        best_performance = all_df.iloc[0]["performance_2m_pct"]

    stats = {
        "fmp_earnings_found": len(fmp_earnings),
        "finnhub_earnings_found": len(finnhub_earnings),
        "candidates_total": len(candidates),
        "stocks_with_price_data": len(all_df),
        "hits": len(filtered_df),
        "skipped_no_symbol": skipped_no_symbol,
        "skipped_no_prices": skipped_no_prices,
        "start_date": str(start_date),
        "end_date": str(end_date),
        "min_performance_2m": min_performance_2m,
        "best_symbol": best_symbol,
        "best_company": best_company,
        "best_performance": best_performance,
    }

    return filtered_df, all_df, stats


if __name__ == "__main__":
    filtered, all_candidates, stats = run_screen()
    print(stats)
    print(filtered)
