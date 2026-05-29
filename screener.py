import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta
from io import StringIO

import pandas as pd
import requests
import streamlit as st

try:
    from tradingview_screener import Query
except Exception:
    Query = None


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

REQUEST_TIMEOUT = 12

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
    "spy_relative_2m_pct",
    "qqq_relative_2m_pct",
    "above_sma_20",
    "above_sma_50",
    "above_sma_150",
    "above_sma_200",
    "distance_sma_50_pct",
    "stage2_score",
    "stage2_status",
    "score",
    "rating",
    "status",
    "interpretation",
    "action",
    "chart_url",
    "data_source",
]


def get_json(url: str):
    response = requests.get(url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.json()


def normalize_symbol(symbol):
    if not symbol:
        return ""

    symbol = str(symbol).upper().strip()

    if ":" in symbol:
        symbol = symbol.split(":")[-1]

    if "." in symbol:
        symbol = symbol.split(".")[0]

    return symbol


def parse_any_date(value):
    if value is None or value == "" or pd.isna(value):
        return None

    try:
        if isinstance(value, (int, float)):
            if value > 10_000_000_000:
                return datetime.utcfromtimestamp(value / 1000).date()
            if value > 1_000_000_000:
                return datetime.utcfromtimestamp(value).date()
            if value > 10_000:
                return pd.to_datetime(str(int(value)), format="%Y%m%d").date()
    except Exception:
        pass

    try:
        parsed = pd.to_datetime(value, errors="coerce", utc=False)

        if pd.isna(parsed):
            return None

        return parsed.date()
    except Exception:
        return None


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


def get_tradingview_earnings_calendar(start_date, end_date, limit=3000):
    if Query is None:
        return [], "tradingview-screener ist nicht installiert oder konnte nicht importiert werden."

    try:
        _, df = (
            Query()
            .select(
                "name",
                "description",
                "exchange",
                "market_cap_basic",
                "close",
                "earnings_release_date",
                "earnings_release_next_date",
            )
            .limit(limit)
            .get_scanner_data()
        )
    except Exception as error:
        return [], f"TradingView Screener Fehler: {error}"

    if df is None or df.empty:
        return [], None

    results = []

    for _, row in df.iterrows():
        raw_ticker = row.get("ticker")
        symbol = normalize_symbol(raw_ticker or row.get("name"))

        if not symbol:
            continue

        company = (
            row.get("description")
            or COMPANY_FALLBACK_MAP.get(symbol)
            or row.get("name")
            or symbol
        )

        exchange = row.get("exchange") or EXCHANGE_FALLBACK_MAP.get(symbol) or "NASDAQ"

        recent_date = parse_any_date(row.get("earnings_release_date"))
        upcoming_date = parse_any_date(row.get("earnings_release_next_date"))

        selected_dates = []

        if recent_date and start_date <= recent_date <= end_date:
            selected_dates.append(("TradingView Recent Earnings", recent_date))

        if upcoming_date and start_date <= upcoming_date <= end_date:
            selected_dates.append(("TradingView Upcoming Earnings", upcoming_date))

        for source, earnings_date in selected_dates:
            results.append(
                {
                    "symbol": symbol,
                    "company": company,
                    "exchange": exchange,
                    "date": str(earnings_date),
                    "source": source,
                }
            )

    return results, None


def add_or_merge_candidate(candidates, symbol, company, exchange, earnings_date, source):
    symbol = normalize_symbol(symbol)

    if not symbol:
        return

    if symbol in candidates:
        old_source = candidates[symbol]["calendar_source"]

        if source not in old_source:
            candidates[symbol]["calendar_source"] = f"{old_source} + {source}"

        if candidates[symbol]["earnings_date"] in ["n/a", None, ""]:
            candidates[symbol]["earnings_date"] = earnings_date

        if candidates[symbol]["company"] in ["n/a", symbol, None, ""]:
            candidates[symbol]["company"] = company or symbol

        return

    candidates[symbol] = {
        "symbol": symbol,
        "company": company or COMPANY_FALLBACK_MAP.get(symbol, symbol),
        "exchange": exchange or EXCHANGE_FALLBACK_MAP.get(symbol, "NASDAQ"),
        "earnings_date": earnings_date or "n/a",
        "calendar_source": source,
    }


def build_candidates_from_calendars(start_date, end_date, use_tradingview=True, tradingview_limit=3000):
    candidates = {}

    fmp_earnings = get_fmp_earnings_calendar(start_date, end_date)
    finnhub_earnings = get_finnhub_earnings_calendar(start_date, end_date)
    tradingview_earnings = []
    tradingview_error = None

    if use_tradingview:
        tradingview_earnings, tradingview_error = get_tradingview_earnings_calendar(
            start_date,
            end_date,
            limit=tradingview_limit,
        )

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

        add_or_merge_candidate(
            candidates=candidates,
            symbol=symbol,
            company=company,
            exchange=EXCHANGE_FALLBACK_MAP.get(symbol, "NASDAQ"),
            earnings_date=earnings_date,
            source="FMP",
        )

    for item in finnhub_earnings:
        symbol = normalize_symbol(item.get("symbol"))

        if not symbol:
            skipped_no_symbol += 1
            continue

        add_or_merge_candidate(
            candidates=candidates,
            symbol=symbol,
            company=COMPANY_FALLBACK_MAP.get(symbol, symbol),
            exchange=EXCHANGE_FALLBACK_MAP.get(symbol, "NASDAQ"),
            earnings_date=item.get("date") or "n/a",
            source="Finnhub",
        )

    for item in tradingview_earnings:
        symbol = normalize_symbol(item.get("symbol"))

        if not symbol:
            skipped_no_symbol += 1
            continue

        add_or_merge_candidate(
            candidates=candidates,
            symbol=symbol,
            company=item.get("company") or COMPANY_FALLBACK_MAP.get(symbol, symbol),
            exchange=item.get("exchange") or EXCHANGE_FALLBACK_MAP.get(symbol, "NASDAQ"),
            earnings_date=item.get("date") or "n/a",
            source="TradingView",
        )

    return (
        candidates,
        fmp_earnings,
        finnhub_earnings,
        tradingview_earnings,
        tradingview_error,
        skipped_no_symbol,
    )


@st.cache_data(ttl=86400, show_spinner=False)
def get_company_profile_cached(symbol):
    symbol = normalize_symbol(symbol)

    fmp_url = (
        "https://financialmodelingprep.com/stable/profile"
        f"?symbol={symbol}&apikey={FMP_API_KEY}"
    )

    try:
        data = get_json(fmp_url)

        if isinstance(data, list) and data:
            item = data[0]
        elif isinstance(data, dict):
            item = data
        else:
            item = {}

        if item:
            return {
                "company": (
                    item.get("companyName")
                    or item.get("companyNameLong")
                    or item.get("name")
                    or COMPANY_FALLBACK_MAP.get(symbol)
                    or symbol
                ),
                "isin": item.get("isin") or item.get("ISIN") or "n/a",
                "exchange": (
                    item.get("exchangeShortName")
                    or item.get("exchange")
                    or EXCHANGE_FALLBACK_MAP.get(symbol)
                    or "NASDAQ"
                ),
            }
    except Exception:
        pass

    finnhub_url = (
        "https://finnhub.io/api/v1/stock/profile2"
        f"?symbol={symbol}&token={FINNHUB_API_KEY}"
    )

    try:
        data = get_json(finnhub_url)

        if isinstance(data, dict) and data:
            return {
                "company": data.get("name") or COMPANY_FALLBACK_MAP.get(symbol) or symbol,
                "isin": data.get("isin") or "n/a",
                "exchange": data.get("exchange") or EXCHANGE_FALLBACK_MAP.get(symbol) or "NASDAQ",
            }
    except Exception:
        pass

    return {
        "company": COMPANY_FALLBACK_MAP.get(symbol) or symbol,
        "isin": "n/a",
        "exchange": EXCHANGE_FALLBACK_MAP.get(symbol) or "NASDAQ",
    }


@st.cache_data(ttl=3600, show_spinner=False)
def get_historical_prices_from_fmp_cached(symbol):
    symbol = normalize_symbol(symbol)

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


@st.cache_data(ttl=3600, show_spinner=False)
def get_historical_prices_from_stooq_cached(symbol):
    symbol = normalize_symbol(symbol).lower()

    url = f"https://stooq.com/q/d/l/?s={symbol}.us&i=d"

    response = requests.get(url, timeout=REQUEST_TIMEOUT)
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
        df = get_historical_prices_from_fmp_cached(symbol)

        if df is not None and len(df) >= 220:
            return df
    except Exception as error:
        print(f"FMP-Kursdaten fehlgeschlagen bei {symbol}: {error}")

    try:
        df = get_historical_prices_from_stooq_cached(symbol)

        if df is not None and len(df) >= 220:
            return df
    except Exception as error:
        print(f"Stooq-Kursdaten fehlgeschlagen bei {symbol}: {error}")

    return None


def calculate_price_performance(df, periods):
    if df is None or len(df) <= periods:
        return None

    current_close = float(df.iloc[-1]["close"])
    past_close = float(df.iloc[-periods - 1]["close"])

    if past_close <= 0:
        return None

    return (current_close / past_close - 1) * 100


def calculate_stage2(df, stock_vs_spy_2m):
    if df is None or len(df) < 220:
        return {
            "stage2_score": 0,
            "stage2_status": "zu wenig Daten",
            "above_sma_150": False,
            "above_sma_200": False,
        }

    close = df["close"]
    current_close = float(close.iloc[-1])

    sma50 = close.tail(50).mean()
    sma150 = close.tail(150).mean()
    sma200 = close.tail(200).mean()
    sma200_20_days_ago = close.iloc[-220:-20].mean()

    high_52w = close.tail(252).max() if len(close) >= 252 else close.max()
    low_52w = close.tail(252).min() if len(close) >= 252 else close.min()

    checks = {
        "price_above_sma50": current_close > sma50,
        "price_above_sma150": current_close > sma150,
        "price_above_sma200": current_close > sma200,
        "sma50_above_sma150": sma50 > sma150,
        "sma150_above_sma200": sma150 > sma200,
        "sma200_rising": sma200 > sma200_20_days_ago,
        "price_near_high": current_close >= high_52w * 0.75,
        "price_above_low": current_close >= low_52w * 1.30,
        "outperforming_spy": stock_vs_spy_2m is not None and stock_vs_spy_2m > 0,
    }

    passed = sum(1 for value in checks.values() if value)
    stage2_score = round((passed / len(checks)) * 100, 0)

    if stage2_score >= 80:
        stage2_status = "Stage 2 stark"
    elif stage2_score >= 60:
        stage2_status = "Stage 2 möglich"
    elif stage2_score >= 40:
        stage2_status = "Trend gemischt"
    else:
        stage2_status = "kein Stage-2-Trend"

    return {
        "stage2_score": stage2_score,
        "stage2_status": stage2_status,
        "above_sma_150": checks["price_above_sma150"],
        "above_sma_200": checks["price_above_sma200"],
    }


def calculate_momentum(df, spy_perf_2m=None, qqq_perf_2m=None):
    if df is None or len(df) < 220:
        return None

    current_close = float(df.iloc[-1]["close"])

    performance_2m = calculate_price_performance(df, 42)

    if performance_2m is None:
        return None

    close = df["close"]

    sma20 = close.tail(20).mean()
    sma50 = close.tail(50).mean()
    sma150 = close.tail(150).mean()
    sma200 = close.tail(200).mean()

    if sma50 <= 0:
        return None

    spy_relative_2m = None
    qqq_relative_2m = None

    if spy_perf_2m is not None:
        spy_relative_2m = performance_2m - spy_perf_2m

    if qqq_perf_2m is not None:
        qqq_relative_2m = performance_2m - qqq_perf_2m

    stage2 = calculate_stage2(df, spy_relative_2m)

    data_source = "n/a"

    if "data_source" in df.columns:
        data_source = str(df.iloc[-1]["data_source"])

    return {
        "current_close": current_close,
        "performance_2m": performance_2m,
        "spy_relative_2m": spy_relative_2m,
        "qqq_relative_2m": qqq_relative_2m,
        "above_sma_20": current_close > sma20,
        "above_sma_50": current_close > sma50,
        "above_sma_150": current_close > sma150,
        "above_sma_200": current_close > sma200,
        "distance_sma_50": (current_close / sma50 - 1) * 100,
        "stage2_score": stage2["stage2_score"],
        "stage2_status": stage2["stage2_status"],
        "data_source": data_source,
    }


def score_stock(momentum):
    score = 0

    if momentum["performance_2m"] >= 15:
        score += 25

    if momentum["performance_2m"] >= 25:
        score += 10

    if momentum["above_sma_20"]:
        score += 10

    if momentum["above_sma_50"]:
        score += 10

    if momentum["above_sma_150"]:
        score += 10

    if momentum["above_sma_200"]:
        score += 10

    if momentum["spy_relative_2m"] is not None and momentum["spy_relative_2m"] > 0:
        score += 10

    if momentum["qqq_relative_2m"] is not None and momentum["qqq_relative_2m"] > 0:
        score += 5

    if momentum["stage2_score"] >= 80:
        score += 10
    elif momentum["stage2_score"] >= 60:
        score += 5

    score = min(score, 100)

    if score >= 80:
        rating = "A"
    elif score >= 65:
        rating = "B"
    elif score >= 50:
        rating = "C"
    else:
        rating = "Watch"

    return score, rating


def classify_stock(performance, min_performance, spy_relative, stage2_score):
    if performance >= min_performance and spy_relative is not None and spy_relative > 0 and stage2_score >= 60:
        return (
            "Treffer",
            "Momentum-Setup mit relativer Stärke und akzeptabler Trendqualität.",
            "Detailanalyse prüfen",
        )

    if performance >= min_performance:
        return (
            "Treffer",
            "Aktie erfüllt den Momentum-Filter, aber relative Stärke oder Stage-2-Qualität sollte geprüft werden.",
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
    profile = get_company_profile_cached(symbol)

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
    spy_relative = momentum.get("spy_relative_2m")
    qqq_relative = momentum.get("qqq_relative_2m")
    stage2_score = momentum.get("stage2_score", 0)

    status, interpretation, action = classify_stock(
        performance,
        min_performance,
        spy_relative,
        stage2_score,
    )

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
        "spy_relative_2m_pct": round(spy_relative, 2) if spy_relative is not None else None,
        "qqq_relative_2m_pct": round(qqq_relative, 2) if qqq_relative is not None else None,
        "above_sma_20": momentum["above_sma_20"],
        "above_sma_50": momentum["above_sma_50"],
        "above_sma_150": momentum["above_sma_150"],
        "above_sma_200": momentum["above_sma_200"],
        "distance_sma_50_pct": round(momentum["distance_sma_50"], 2),
        "stage2_score": int(momentum["stage2_score"]),
        "stage2_status": momentum["stage2_status"],
        "score": score,
        "rating": rating,
        "status": status,
        "interpretation": interpretation,
        "action": action,
        "chart_url": chart_url(symbol, exchange),
        "data_source": momentum.get("data_source", "n/a"),
    }


def evaluate_symbol(candidate, spy_perf_2m, qqq_perf_2m, min_performance_2m):
    symbol = candidate["symbol"]

    prices = get_historical_prices(symbol)
    momentum = calculate_momentum(prices, spy_perf_2m, qqq_perf_2m)

    if momentum is None:
        return None

    return build_result_row(
        symbol=symbol,
        company=candidate["company"],
        earnings_date=candidate["earnings_date"],
        calendar_source=candidate["calendar_source"],
        momentum=momentum,
        min_performance=min_performance_2m,
    )


def analyze_single_symbol(symbol, min_performance_2m=15.0):
    symbol = normalize_symbol(symbol)

    if not symbol:
        return None

    try:
        spy_df = get_historical_prices("SPY")
        qqq_df = get_historical_prices("QQQ")

        spy_perf_2m = calculate_price_performance(spy_df, 42)
        qqq_perf_2m = calculate_price_performance(qqq_df, 42)

        prices = get_historical_prices(symbol)
        momentum = calculate_momentum(prices, spy_perf_2m, qqq_perf_2m)

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


def calculate_market_regime():
    spy_df = get_historical_prices("SPY")
    qqq_df = get_historical_prices("QQQ")

    spy_perf_2m = calculate_price_performance(spy_df, 42)
    qqq_perf_2m = calculate_price_performance(qqq_df, 42)

    def index_status(df, name):
        if df is None or len(df) < 220:
            return {
                "name": name,
                "status": "unbekannt",
                "above_sma50": False,
                "above_sma200": False,
                "perf_2m": None,
            }

        close = df["close"]
        current = float(close.iloc[-1])
        sma50 = close.tail(50).mean()
        sma200 = close.tail(200).mean()
        perf_2m = calculate_price_performance(df, 42)

        if current > sma50 and current > sma200:
            status = "grün"
        elif current > sma200:
            status = "neutral"
        else:
            status = "rot"

        return {
            "name": name,
            "status": status,
            "above_sma50": current > sma50,
            "above_sma200": current > sma200,
            "perf_2m": round(perf_2m, 2) if perf_2m is not None else None,
        }

    spy_status = index_status(spy_df, "SPY")
    qqq_status = index_status(qqq_df, "QQQ")

    if spy_status["status"] == "grün" and qqq_status["status"] == "grün":
        regime = "grün"
        interpretation = "Marktumfeld unterstützt Momentum-Setups."
    elif spy_status["status"] == "rot" or qqq_status["status"] == "rot":
        regime = "rot"
        interpretation = "Marktumfeld ist riskant. Earnings-Breakouts können schneller scheitern."
    else:
        regime = "neutral"
        interpretation = "Marktumfeld ist gemischt. Positionsgröße und Risikomanagement wichtiger."

    return {
        "regime": regime,
        "interpretation": interpretation,
        "spy_status": spy_status,
        "qqq_status": qqq_status,
        "spy_perf_2m": spy_perf_2m,
        "qqq_perf_2m": qqq_perf_2m,
    }


def run_screen(
    lookback_days=7,
    forward_days=14,
    min_performance_2m=15.0,
    use_tradingview=True,
    tradingview_limit=3000,
    max_candidates=250,
    max_workers=12,
    progress_callback=None,
):
    os.makedirs(DATA_DIR, exist_ok=True)

    today = date.today()
    start_date = today - timedelta(days=lookback_days)
    end_date = today + timedelta(days=forward_days)

    (
        candidates,
        fmp_earnings,
        finnhub_earnings,
        tradingview_earnings,
        tradingview_error,
        skipped_no_symbol,
    ) = build_candidates_from_calendars(
        start_date=start_date,
        end_date=end_date,
        use_tradingview=use_tradingview,
        tradingview_limit=tradingview_limit,
    )

    candidate_items = list(candidates.items())

    original_candidates_total = len(candidate_items)

    if max_candidates and len(candidate_items) > max_candidates:
        candidate_items = candidate_items[:max_candidates]

    market_regime = calculate_market_regime()
    spy_perf_2m = market_regime.get("spy_perf_2m")
    qqq_perf_2m = market_regime.get("qqq_perf_2m")

    all_results = []
    skipped_no_prices = 0

    total = len(candidate_items)
    done = 0

    if progress_callback:
        progress_callback(done, total)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                evaluate_symbol,
                candidate,
                spy_perf_2m,
                qqq_perf_2m,
                min_performance_2m,
            ): symbol
            for symbol, candidate in candidate_items
        }

        for future in as_completed(futures):
            symbol = futures[future]

            try:
                row = future.result()

                if row is None:
                    skipped_no_prices += 1
                else:
                    all_results.append(row)
            except Exception as error:
                skipped_no_prices += 1
                print(f"Fehler bei {symbol}: {error}")

            done += 1

            if progress_callback:
                progress_callback(done, total)

    all_df = pd.DataFrame(all_results, columns=COLUMNS)

    if not all_df.empty:
        all_df = all_df.sort_values(
            by=["score", "performance_2m_pct", "stage2_score"],
            ascending=[False, False, False],
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
        "tradingview_earnings_found": len(tradingview_earnings),
        "tradingview_error": tradingview_error,
        "candidates_total": original_candidates_total,
        "candidates_scanned": len(candidate_items),
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
        "market_regime": market_regime,
    }

    return filtered_df, all_df, stats


if __name__ == "__main__":
    filtered, all_candidates, stats = run_screen()
    print(stats)
    print(filtered)
