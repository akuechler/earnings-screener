import os
from datetime import date, datetime, timedelta

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
    raise RuntimeError("FMP_API_KEY fehlt.")

if not FINNHUB_API_KEY:
    raise RuntimeError("FINNHUB_API_KEY fehlt.")


DATA_DIR = "data"
FILTERED_FILE = f"{DATA_DIR}/earnings_momentum_screen.csv"
ALL_FILE = f"{DATA_DIR}/earnings_momentum_all.csv"

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
    "performance_1m_pct",
    "performance_3m_pct",
    "performance_2m_proxy_pct",
    "spy_relative_proxy_pct",
    "qqq_relative_proxy_pct",
    "above_sma_50",
    "above_sma_200",
    "distance_sma_50_pct",
    "distance_sma_200_pct",
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


def normalize_symbol(symbol):
    if not symbol:
        return ""

    symbol = str(symbol).upper().strip()

    if ":" in symbol:
        symbol = symbol.split(":")[-1]

    if "." in symbol:
        symbol = symbol.split(".")[0]

    return symbol


def normalize_exchange(exchange):
    if not exchange:
        return "NASDAQ"

    exchange = str(exchange).upper().strip()

    if "NASDAQ" in exchange:
        return "NASDAQ"

    if "NYSE" in exchange or "NEW YORK" in exchange:
        return "NYSE"

    if "AMEX" in exchange:
        return "AMEX"

    return exchange


def tradingview_url(symbol, exchange):
    symbol = normalize_symbol(symbol)
    exchange = normalize_exchange(exchange)

    return f"https://www.tradingview.com/chart/?symbol={exchange}%3A{symbol}"


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


def safe_number(value):
    try:
        if value is None or pd.isna(value):
            return None

        return float(value)
    except Exception:
        return None


def get_json(url):
    response = requests.get(url, timeout=12)
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
        print(f"FMP Earnings Fehler: {error}")
        return []

    return data if isinstance(data, list) else []


def get_finnhub_earnings_calendar(start_date, end_date):
    url = (
        "https://finnhub.io/api/v1/calendar/earnings"
        f"?from={start_date}&to={end_date}&token={FINNHUB_API_KEY}"
    )

    try:
        data = get_json(url)
    except Exception as error:
        print(f"Finnhub Earnings Fehler: {error}")
        return []

    if isinstance(data, dict):
        return data.get("earningsCalendar", []) or []

    return []


@st.cache_data(ttl=1800, show_spinner=False)
def get_tradingview_universe(limit=8000):
    if Query is None:
        return pd.DataFrame(), "tradingview-screener ist nicht installiert."

    selected_fields = [
        "name",
        "description",
        "exchange",
        "close",
        "market_cap_basic",
        "Perf.1M",
        "Perf.3M",
        "Perf.6M",
        "Perf.YTD",
        "SMA50",
        "SMA200",
        "earnings_release_date",
        "earnings_release_next_date",
    ]

    try:
        _, df = Query().select(*selected_fields).limit(limit).get_scanner_data()
    except Exception as error:
        return pd.DataFrame(), f"TradingView Screener Fehler: {error}"

    if df is None:
        return pd.DataFrame(), None

    return df, None


def get_tradingview_earnings_candidates(start_date, end_date, limit=8000):
    df, error = get_tradingview_universe(limit=limit)

    if df.empty:
        return [], error

    results = []

    for _, row in df.iterrows():
        raw_ticker = row.get("ticker") or row.get("name")
        symbol = normalize_symbol(raw_ticker)

        if not symbol:
            continue

        company = (
            row.get("description")
            or COMPANY_FALLBACK_MAP.get(symbol)
            or symbol
        )

        exchange = normalize_exchange(row.get("exchange") or EXCHANGE_FALLBACK_MAP.get(symbol))

        recent_date = parse_any_date(row.get("earnings_release_date"))
        next_date = parse_any_date(row.get("earnings_release_next_date"))

        used_date = None
        source = None

        if recent_date and start_date <= recent_date <= end_date:
            used_date = recent_date
            source = "TradingView Recent"

        if next_date and start_date <= next_date <= end_date:
            used_date = next_date
            source = "TradingView Upcoming"

        if used_date is None:
            continue

        perf_1m = safe_number(row.get("Perf.1M"))
        perf_3m = safe_number(row.get("Perf.3M"))
        perf_6m = safe_number(row.get("Perf.6M"))
        close = safe_number(row.get("close"))
        sma50 = safe_number(row.get("SMA50"))
        sma200 = safe_number(row.get("SMA200"))
        market_cap = safe_number(row.get("market_cap_basic"))

        results.append(
            {
                "symbol": symbol,
                "company": company,
                "exchange": exchange,
                "earnings_date": str(used_date),
                "calendar_source": source,
                "current_close": close,
                "performance_1m_pct": perf_1m,
                "performance_3m_pct": perf_3m,
                "performance_6m_pct": perf_6m,
                "sma50": sma50,
                "sma200": sma200,
                "market_cap": market_cap,
                "raw_source": "TradingView",
            }
        )

    return results, error


def get_fmp_finnhub_candidates(start_date, end_date):
    fmp = get_fmp_earnings_calendar(start_date, end_date)
    finnhub = get_finnhub_earnings_calendar(start_date, end_date)

    candidates = []

    for item in fmp:
        symbol = normalize_symbol(item.get("symbol"))

        if not symbol:
            continue

        candidates.append(
            {
                "symbol": symbol,
                "company": item.get("companyName") or item.get("name") or item.get("company") or COMPANY_FALLBACK_MAP.get(symbol) or symbol,
                "exchange": EXCHANGE_FALLBACK_MAP.get(symbol, "NASDAQ"),
                "earnings_date": item.get("date") or "n/a",
                "calendar_source": "FMP",
                "current_close": None,
                "performance_1m_pct": None,
                "performance_3m_pct": None,
                "performance_6m_pct": None,
                "sma50": None,
                "sma200": None,
                "market_cap": None,
                "raw_source": "FMP",
            }
        )

    for item in finnhub:
        symbol = normalize_symbol(item.get("symbol"))

        if not symbol:
            continue

        candidates.append(
            {
                "symbol": symbol,
                "company": COMPANY_FALLBACK_MAP.get(symbol) or symbol,
                "exchange": EXCHANGE_FALLBACK_MAP.get(symbol, "NASDAQ"),
                "earnings_date": item.get("date") or "n/a",
                "calendar_source": "Finnhub",
                "current_close": None,
                "performance_1m_pct": None,
                "performance_3m_pct": None,
                "performance_6m_pct": None,
                "sma50": None,
                "sma200": None,
                "market_cap": None,
                "raw_source": "Finnhub",
            }
        )

    return candidates, fmp, finnhub


def merge_candidates(*candidate_lists):
    merged = {}

    for candidate_list in candidate_lists:
        for item in candidate_list:
            symbol = normalize_symbol(item.get("symbol"))

            if not symbol:
                continue

            if symbol not in merged:
                merged[symbol] = dict(item)
                continue

            old = merged[symbol]

            old_source = old.get("calendar_source", "")
            new_source = item.get("calendar_source", "")

            if new_source and new_source not in old_source:
                old["calendar_source"] = f"{old_source} + {new_source}"

            for field in [
                "company",
                "exchange",
                "earnings_date",
                "current_close",
                "performance_1m_pct",
                "performance_3m_pct",
                "performance_6m_pct",
                "sma50",
                "sma200",
                "market_cap",
            ]:
                if old.get(field) in [None, "", "n/a"]:
                    old[field] = item.get(field)

    return list(merged.values())


def estimate_2m_from_1m_3m(perf_1m, perf_3m):
    if perf_1m is not None and perf_3m is not None:
        return round((perf_1m + perf_3m) / 2, 2)

    if perf_3m is not None:
        return round(perf_3m * (2 / 3), 2)

    if perf_1m is not None:
        return round(perf_1m, 2)

    return None


def get_index_performance_from_tradingview(symbol):
    df, _ = get_tradingview_universe(limit=10000)

    if df.empty:
        return None

    candidates = df[df["name"].astype(str).str.upper() == symbol.upper()]

    if candidates.empty and "ticker" in df.columns:
        candidates = df[df["ticker"].astype(str).str.upper().str.endswith(f":{symbol.upper()}")]

    if candidates.empty:
        return None

    row = candidates.iloc[0]

    perf_1m = safe_number(row.get("Perf.1M"))
    perf_3m = safe_number(row.get("Perf.3M"))

    return estimate_2m_from_1m_3m(perf_1m, perf_3m)


def calculate_market_regime():
    spy_perf = get_index_performance_from_tradingview("SPY")
    qqq_perf = get_index_performance_from_tradingview("QQQ")

    if spy_perf is None and qqq_perf is None:
        return {
            "regime": "unbekannt",
            "interpretation": "SPY/QQQ konnten nicht aus TradingView gelesen werden.",
            "spy_perf_2m": None,
            "qqq_perf_2m": None,
        }

    if (spy_perf is not None and spy_perf > 5) and (qqq_perf is not None and qqq_perf > 5):
        regime = "grün"
        interpretation = "Marktumfeld unterstützt Momentum-Setups."
    elif (spy_perf is not None and spy_perf < -3) or (qqq_perf is not None and qqq_perf < -3):
        regime = "rot"
        interpretation = "Marktumfeld ist riskant. Breakouts können schneller scheitern."
    else:
        regime = "neutral"
        interpretation = "Marktumfeld ist gemischt. Positionsgröße und Risikomanagement wichtiger."

    return {
        "regime": regime,
        "interpretation": interpretation,
        "spy_perf_2m": round(spy_perf, 2) if spy_perf is not None else None,
        "qqq_perf_2m": round(qqq_perf, 2) if qqq_perf is not None else None,
    }


def calculate_stage2_score(close, sma50, sma200, perf_3m, perf_6m, spy_relative):
    checks = {
        "price_above_sma50": close is not None and sma50 is not None and close > sma50,
        "price_above_sma200": close is not None and sma200 is not None and close > sma200,
        "sma50_above_sma200": sma50 is not None and sma200 is not None and sma50 > sma200,
        "perf_3m_positive": perf_3m is not None and perf_3m > 0,
        "perf_6m_positive": perf_6m is not None and perf_6m > 0,
        "perf_3m_strong": perf_3m is not None and perf_3m > 10,
        "outperforming_spy": spy_relative is not None and spy_relative > 0,
    }

    passed = sum(1 for value in checks.values() if value)
    score = round((passed / len(checks)) * 100, 0)

    if score >= 80:
        status = "Stage 2 stark"
    elif score >= 60:
        status = "Stage 2 möglich"
    elif score >= 40:
        status = "Trend gemischt"
    else:
        status = "kein Stage-2-Trend"

    return int(score), status


def classify_stock(perf_2m, min_perf, spy_relative, stage2_score):
    if perf_2m is None:
        return "Keine Daten", "Keine verwertbare Performance aus TradingView.", "Ignorieren"

    if perf_2m >= min_perf and spy_relative is not None and spy_relative > 0 and stage2_score >= 60:
        return (
            "Treffer",
            "Momentum-Setup mit relativer Stärke und akzeptabler Trendqualität.",
            "Detailanalyse prüfen",
        )

    if perf_2m >= min_perf:
        return (
            "Treffer",
            "Aktie erfüllt den Momentum-Filter. Relative Stärke und Trendqualität prüfen.",
            "Detailanalyse prüfen",
        )

    if perf_2m >= min_perf - 5:
        return (
            "Knapp darunter",
            "Nahe am Momentum-Filter, aber noch kein klares Setup.",
            "Watchlist",
        )

    if perf_2m >= 5:
        return (
            "Unter Filter",
            "Positives Momentum, aber zu schwach für dein Setup.",
            "Nur beobachten",
        )

    if perf_2m >= 0:
        return (
            "Unter Filter",
            "Kaum Momentum. Kein klarer institutioneller Vorlauf.",
            "Ignorieren",
        )

    return (
        "Schwach",
        "Negatives Momentum. Für diesen Ansatz uninteressant.",
        "Ignorieren",
    )


def score_stock(perf_2m, spy_relative, qqq_relative, stage2_score, close, sma50, sma200):
    score = 0

    if perf_2m is not None and perf_2m >= 15:
        score += 25

    if perf_2m is not None and perf_2m >= 25:
        score += 10

    if spy_relative is not None and spy_relative > 0:
        score += 15

    if qqq_relative is not None and qqq_relative > 0:
        score += 10

    if close is not None and sma50 is not None and close > sma50:
        score += 10

    if close is not None and sma200 is not None and close > sma200:
        score += 10

    if stage2_score >= 80:
        score += 15
    elif stage2_score >= 60:
        score += 8

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


def build_result_row(candidate, min_performance, spy_perf, qqq_perf):
    symbol = normalize_symbol(candidate.get("symbol"))
    company = candidate.get("company") or COMPANY_FALLBACK_MAP.get(symbol) or symbol
    exchange = normalize_exchange(candidate.get("exchange") or EXCHANGE_FALLBACK_MAP.get(symbol))

    perf_1m = safe_number(candidate.get("performance_1m_pct"))
    perf_3m = safe_number(candidate.get("performance_3m_pct"))
    perf_6m = safe_number(candidate.get("performance_6m_pct"))
    perf_2m = estimate_2m_from_1m_3m(perf_1m, perf_3m)

    close = safe_number(candidate.get("current_close"))
    sma50 = safe_number(candidate.get("sma50"))
    sma200 = safe_number(candidate.get("sma200"))

    spy_relative = None
    qqq_relative = None

    if perf_2m is not None and spy_perf is not None:
        spy_relative = round(perf_2m - spy_perf, 2)

    if perf_2m is not None and qqq_perf is not None:
        qqq_relative = round(perf_2m - qqq_perf, 2)

    distance_sma50 = None
    distance_sma200 = None

    if close is not None and sma50 is not None and sma50 > 0:
        distance_sma50 = round((close / sma50 - 1) * 100, 2)

    if close is not None and sma200 is not None and sma200 > 0:
        distance_sma200 = round((close / sma200 - 1) * 100, 2)

    stage2_score, stage2_status = calculate_stage2_score(
        close=close,
        sma50=sma50,
        sma200=sma200,
        perf_3m=perf_3m,
        perf_6m=perf_6m,
        spy_relative=spy_relative,
    )

    score, rating = score_stock(
        perf_2m=perf_2m,
        spy_relative=spy_relative,
        qqq_relative=qqq_relative,
        stage2_score=stage2_score,
        close=close,
        sma50=sma50,
        sma200=sma200,
    )

    status, interpretation, action = classify_stock(
        perf_2m=perf_2m,
        min_perf=min_performance,
        spy_relative=spy_relative,
        stage2_score=stage2_score,
    )

    return {
        "symbol": symbol,
        "company": company,
        "wkn": WKN_MAP.get(symbol, "n/a"),
        "isin": "n/a",
        "exchange": exchange,
        "earnings_date": candidate.get("earnings_date") or "n/a",
        "calendar_source": candidate.get("calendar_source") or "n/a",
        "current_close": close,
        "performance_1m_pct": round(perf_1m, 2) if perf_1m is not None else None,
        "performance_3m_pct": round(perf_3m, 2) if perf_3m is not None else None,
        "performance_2m_proxy_pct": perf_2m,
        "spy_relative_proxy_pct": spy_relative,
        "qqq_relative_proxy_pct": qqq_relative,
        "above_sma_50": close is not None and sma50 is not None and close > sma50,
        "above_sma_200": close is not None and sma200 is not None and close > sma200,
        "distance_sma_50_pct": distance_sma50,
        "distance_sma_200_pct": distance_sma200,
        "stage2_score": stage2_score,
        "stage2_status": stage2_status,
        "score": score,
        "rating": rating,
        "status": status,
        "interpretation": interpretation,
        "action": action,
        "chart_url": tradingview_url(symbol, exchange),
        "data_source": "TradingView Screener",
    }


def analyze_single_symbol(symbol, min_performance_2m=15.0):
    symbol = normalize_symbol(symbol)

    if not symbol:
        return None

    df, error = get_tradingview_universe(limit=10000)

    if error or df.empty:
        return None

    match = df[df["name"].astype(str).str.upper() == symbol]

    if match.empty and "ticker" in df.columns:
        match = df[df["ticker"].astype(str).str.upper().str.endswith(f":{symbol}")]

    if match.empty:
        return None

    row = match.iloc[0]

    candidate = {
        "symbol": symbol,
        "company": row.get("description") or COMPANY_FALLBACK_MAP.get(symbol) or symbol,
        "exchange": row.get("exchange") or EXCHANGE_FALLBACK_MAP.get(symbol) or "NASDAQ",
        "earnings_date": "nicht geprüft",
        "calendar_source": "Manuelle TradingView-Prüfung",
        "current_close": safe_number(row.get("close")),
        "performance_1m_pct": safe_number(row.get("Perf.1M")),
        "performance_3m_pct": safe_number(row.get("Perf.3M")),
        "performance_6m_pct": safe_number(row.get("Perf.6M")),
        "sma50": safe_number(row.get("SMA50")),
        "sma200": safe_number(row.get("SMA200")),
    }

    market = calculate_market_regime()
    spy_perf = market.get("spy_perf_2m")
    qqq_perf = market.get("qqq_perf_2m")

    result = build_result_row(candidate, min_performance_2m, spy_perf, qqq_perf)

    return pd.DataFrame([result], columns=COLUMNS)


def run_screen(
    lookback_days=7,
    forward_days=14,
    min_performance_2m=15.0,
    tradingview_limit=8000,
):
    today = date.today()
    start_date = today - timedelta(days=lookback_days)
    end_date = today + timedelta(days=forward_days)

    tv_candidates, tv_error = get_tradingview_earnings_candidates(
        start_date=start_date,
        end_date=end_date,
        limit=tradingview_limit,
    )

    api_candidates, fmp_earnings, finnhub_earnings = get_fmp_finnhub_candidates(
        start_date=start_date,
        end_date=end_date,
    )

    candidates = merge_candidates(tv_candidates, api_candidates)

    market_regime = calculate_market_regime()
    spy_perf = market_regime.get("spy_perf_2m")
    qqq_perf = market_regime.get("qqq_perf_2m")

    rows = []

    for candidate in candidates:
        row = build_result_row(
            candidate=candidate,
            min_performance=min_performance_2m,
            spy_perf=spy_perf,
            qqq_perf=qqq_perf,
        )

        if row["performance_2m_proxy_pct"] is not None:
            rows.append(row)

    all_df = pd.DataFrame(rows, columns=COLUMNS)

    if not all_df.empty:
        all_df = all_df.sort_values(
            by=["score", "performance_2m_proxy_pct", "stage2_score"],
            ascending=[False, False, False],
        )

    filtered_df = all_df[
        all_df["performance_2m_proxy_pct"] >= min_performance_2m
    ].copy()

    best_symbol = None
    best_company = None
    best_performance = None

    if not all_df.empty:
        best_symbol = all_df.iloc[0]["symbol"]
        best_company = all_df.iloc[0]["company"]
        best_performance = all_df.iloc[0]["performance_2m_proxy_pct"]

    stats = {
        "fmp_earnings_found": len(fmp_earnings),
        "finnhub_earnings_found": len(finnhub_earnings),
        "tradingview_earnings_found": len(tv_candidates),
        "tradingview_error": tv_error,
        "candidates_total": len(candidates),
        "stocks_with_price_data": len(all_df),
        "hits": len(filtered_df),
        "start_date": str(start_date),
        "end_date": str(end_date),
        "min_performance_2m": min_performance_2m,
        "best_symbol": best_symbol,
        "best_company": best_company,
        "best_performance": best_performance,
        "market_regime": market_regime,
    }

    return filtered_df, all_df, stats
