import os
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
    "sector",
    "industry",
    "setup_type",
    "earnings_date",
    "calendar_source",
    "current_close",
    "market_cap",
    "market_cap_m",
    "volume",
    "dollar_volume_m",
    "performance_1m_pct",
    "performance_3m_pct",
    "performance_6m_pct",
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
    "quality_pass",
    "quality_reason",
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
        return "UNKNOWN"

    exchange = str(exchange).upper().strip()

    if "NASDAQ" in exchange:
        return "NASDAQ"

    if "NYSE" in exchange or "NEW YORK" in exchange:
        return "NYSE"

    if "AMEX" in exchange:
        return "AMEX"

    if "OTC" in exchange or "PINK" in exchange:
        return "OTC"

    return exchange


def tradingview_url(symbol, exchange):
    symbol = normalize_symbol(symbol)
    exchange = normalize_exchange(exchange)

    if exchange == "UNKNOWN":
        exchange = EXCHANGE_FALLBACK_MAP.get(symbol, "NASDAQ")

    return f"https://www.tradingview.com/chart/?symbol={exchange}%3A{symbol}"


def safe_number(value):
    try:
        if value is None or pd.isna(value):
            return None

        return float(value)
    except Exception:
        return None


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


def get_json(url):
    response = requests.get(url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.json()


def get_fmp_earnings_calendar(start_date, end_date):
    if not FMP_API_KEY:
        return []

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
    if not FINNHUB_API_KEY:
        return []

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

    field_sets = [
        [
            "name",
            "description",
            "exchange",
            "close",
            "volume",
            "market_cap_basic",
            "Perf.1M",
            "Perf.3M",
            "Perf.6M",
            "Perf.YTD",
            "SMA50",
            "SMA200",
            "earnings_release_date",
            "earnings_release_next_date",
            "sector",
            "industry",
        ],
        [
            "name",
            "description",
            "exchange",
            "close",
            "volume",
            "market_cap_basic",
            "Perf.1M",
            "Perf.3M",
            "Perf.6M",
            "SMA50",
            "SMA200",
            "earnings_release_date",
            "earnings_release_next_date",
        ],
        [
            "name",
            "description",
            "exchange",
            "close",
            "volume",
            "Perf.1M",
            "Perf.3M",
            "Perf.6M",
            "SMA50",
            "SMA200",
            "earnings_release_date",
            "earnings_release_next_date",
        ],
    ]

    last_error = None

    for fields in field_sets:
        try:
            _, df = Query().select(*fields).limit(limit).get_scanner_data()

            if df is None:
                return pd.DataFrame(), None

            return df, None

        except Exception as error:
            last_error = error

    return pd.DataFrame(), f"TradingView Screener Fehler: {last_error}"


def row_get(row, candidates):
    for field in candidates:
        if field in row and not pd.isna(row[field]):
            return row[field]

    return None


def estimate_2m_from_1m_3m(perf_1m, perf_3m):
    if perf_1m is not None and perf_3m is not None:
        return round((perf_1m + perf_3m) / 2, 2)

    if perf_3m is not None:
        return round(perf_3m * (2 / 3), 2)

    if perf_1m is not None:
        return round(perf_1m, 2)

    return None


@st.cache_data(ttl=1800, show_spinner=False)
def get_stooq_history(symbol):
    symbol = str(symbol).lower().strip()

    url = f"https://stooq.com/q/d/l/?s={symbol}.us&i=d"

    try:
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

        if len(df) < 50:
            return None

        return df
    except Exception:
        return None


def calculate_stooq_performance(symbol, periods=42):
    df = get_stooq_history(symbol)

    if df is None or len(df) <= periods:
        return None

    current = safe_number(df.iloc[-1]["close"])
    past = safe_number(df.iloc[-periods - 1]["close"])

    if current is None or past is None or past <= 0:
        return None

    return round((current / past - 1) * 100, 2)


def calculate_market_proxy():
    spy = calculate_stooq_performance("SPY", 42)
    qqq = calculate_stooq_performance("QQQ", 42)

    return {
        "spy_perf_2m": spy,
        "qqq_perf_2m": qqq,
    }


def build_tv_info_map(tv_df):
    info_map = {}

    if tv_df is None or tv_df.empty:
        return info_map

    for _, row in tv_df.iterrows():
        raw_symbol = row.get("ticker") or row.get("name")
        symbol = normalize_symbol(raw_symbol)

        if not symbol:
            continue

        exchange = normalize_exchange(row_get(row, ["exchange"]) or EXCHANGE_FALLBACK_MAP.get(symbol))
        close = safe_number(row_get(row, ["close"]))
        volume = safe_number(row_get(row, ["volume", "Volume"]))
        market_cap = safe_number(row_get(row, ["market_cap_basic", "market_cap"]))

        info_map[symbol] = {
            "symbol": symbol,
            "company": row_get(row, ["description"]) or COMPANY_FALLBACK_MAP.get(symbol) or symbol,
            "exchange": exchange,
            "sector": row_get(row, ["sector"]) or "n/a",
            "industry": row_get(row, ["industry"]) or "n/a",
            "current_close": close,
            "volume": volume,
            "market_cap": market_cap,
            "performance_1m_pct": safe_number(row_get(row, ["Perf.1M"])),
            "performance_3m_pct": safe_number(row_get(row, ["Perf.3M"])),
            "performance_6m_pct": safe_number(row_get(row, ["Perf.6M"])),
            "sma50": safe_number(row_get(row, ["SMA50"])),
            "sma200": safe_number(row_get(row, ["SMA200"])),
            "recent_earnings_date": parse_any_date(row_get(row, ["earnings_release_date"])),
            "next_earnings_date": parse_any_date(row_get(row, ["earnings_release_next_date"])),
        }

    return info_map


def get_tradingview_earnings_candidates(start_date, end_date, limit=8000):
    tv_df, error = get_tradingview_universe(limit=limit)

    if tv_df.empty:
        return [], {}, error

    tv_info = build_tv_info_map(tv_df)
    candidates = []

    for symbol, info in tv_info.items():
        recent_date = info.get("recent_earnings_date")
        next_date = info.get("next_earnings_date")

        if next_date and start_date <= next_date <= end_date:
            candidate = dict(info)
            candidate["earnings_date"] = str(next_date)
            candidate["calendar_source"] = "TradingView Upcoming"
            candidate["setup_type"] = "Pre-Earnings"
            candidates.append(candidate)

        if recent_date and start_date <= recent_date <= end_date:
            candidate = dict(info)
            candidate["earnings_date"] = str(recent_date)
            candidate["calendar_source"] = "TradingView Recent"
            candidate["setup_type"] = "Post-Earnings"
            candidates.append(candidate)

    return candidates, tv_info, error


def get_api_candidates(start_date, end_date, tv_info):
    fmp = get_fmp_earnings_calendar(start_date, end_date)
    finnhub = get_finnhub_earnings_calendar(start_date, end_date)

    candidates = []

    today = date.today()

    for item in fmp:
        symbol = normalize_symbol(item.get("symbol"))

        if not symbol:
            continue

        earnings_date_raw = item.get("date") or item.get("fiscalDateEnding")
        earnings_date = parse_any_date(earnings_date_raw)
        setup_type = "Pre-Earnings" if earnings_date and earnings_date >= today else "Post-Earnings"

        base = tv_info.get(symbol, {})
        candidate = dict(base)

        candidate.update(
            {
                "symbol": symbol,
                "company": (
                    item.get("companyName")
                    or item.get("name")
                    or item.get("company")
                    or base.get("company")
                    or COMPANY_FALLBACK_MAP.get(symbol)
                    or symbol
                ),
                "exchange": base.get("exchange") or EXCHANGE_FALLBACK_MAP.get(symbol, "UNKNOWN"),
                "sector": base.get("sector", "n/a"),
                "industry": base.get("industry", "n/a"),
                "earnings_date": str(earnings_date) if earnings_date else "n/a",
                "calendar_source": "FMP",
                "setup_type": setup_type,
            }
        )

        candidates.append(candidate)

    for item in finnhub:
        symbol = normalize_symbol(item.get("symbol"))

        if not symbol:
            continue

        earnings_date = parse_any_date(item.get("date"))
        setup_type = "Pre-Earnings" if earnings_date and earnings_date >= today else "Post-Earnings"

        base = tv_info.get(symbol, {})
        candidate = dict(base)

        candidate.update(
            {
                "symbol": symbol,
                "company": base.get("company") or COMPANY_FALLBACK_MAP.get(symbol) or symbol,
                "exchange": base.get("exchange") or EXCHANGE_FALLBACK_MAP.get(symbol, "UNKNOWN"),
                "sector": base.get("sector", "n/a"),
                "industry": base.get("industry", "n/a"),
                "earnings_date": str(earnings_date) if earnings_date else "n/a",
                "calendar_source": "Finnhub",
                "setup_type": setup_type,
            }
        )

        candidates.append(candidate)

    return candidates, fmp, finnhub


def merge_candidates(candidate_lists):
    merged = {}

    for candidates in candidate_lists:
        for candidate in candidates:
            symbol = normalize_symbol(candidate.get("symbol"))
            setup_type = candidate.get("setup_type", "n/a")
            earnings_date = candidate.get("earnings_date", "n/a")
            key = f"{symbol}|{setup_type}|{earnings_date}"

            if not symbol:
                continue

            if key not in merged:
                merged[key] = dict(candidate)
                continue

            old = merged[key]
            old_source = old.get("calendar_source", "")
            new_source = candidate.get("calendar_source", "")

            if new_source and new_source not in old_source:
                old["calendar_source"] = f"{old_source} + {new_source}"

            for field, value in candidate.items():
                if old.get(field) in [None, "", "n/a"] and value not in [None, "", "n/a"]:
                    old[field] = value

    return list(merged.values())


def quality_check(candidate, min_price, min_market_cap_m, min_volume, min_dollar_volume_m, allowed_exchanges, exclude_otc):
    symbol = normalize_symbol(candidate.get("symbol"))
    exchange = normalize_exchange(candidate.get("exchange"))
    close = safe_number(candidate.get("current_close"))
    volume = safe_number(candidate.get("volume"))
    market_cap = safe_number(candidate.get("market_cap"))

    market_cap_m = market_cap / 1_000_000 if market_cap is not None else None
    dollar_volume_m = None

    if close is not None and volume is not None:
        dollar_volume_m = (close * volume) / 1_000_000

    reasons = []

    if exclude_otc and exchange == "OTC":
        reasons.append("OTC ausgeschlossen")

    if allowed_exchanges and exchange not in allowed_exchanges:
        reasons.append(f"Börse {exchange} nicht erlaubt")

    if close is None:
        reasons.append("kein Kurs")
    elif close < min_price:
        reasons.append(f"Kurs unter {min_price:.2f}")

    if market_cap_m is None:
        reasons.append("keine Marktkapitalisierung")
    elif market_cap_m < min_market_cap_m:
        reasons.append(f"Marktkapitalisierung unter {min_market_cap_m:.0f} Mio.")

    if volume is None:
        reasons.append("kein Volumen")
    elif volume < min_volume:
        reasons.append(f"Volumen unter {min_volume:,.0f}")

    if dollar_volume_m is None:
        reasons.append("kein Dollar-Volumen")
    elif dollar_volume_m < min_dollar_volume_m:
        reasons.append(f"Dollar-Volumen unter {min_dollar_volume_m:.0f} Mio.")

    quality_pass = len(reasons) == 0
    quality_reason = "OK" if quality_pass else "; ".join(reasons)

    return quality_pass, quality_reason, market_cap_m, dollar_volume_m


def calculate_stage2_score(close, sma50, sma200, perf_3m, perf_6m, spy_relative, distance_sma50, distance_sma200):
    checks = {
        "price_above_sma50": close is not None and sma50 is not None and close > sma50,
        "price_above_sma200": close is not None and sma200 is not None and close > sma200,
        "sma50_above_sma200": sma50 is not None and sma200 is not None and sma50 > sma200,
        "perf_3m_positive": perf_3m is not None and perf_3m > 0,
        "perf_6m_positive": perf_6m is not None and perf_6m > 0,
        "perf_3m_strong": perf_3m is not None and perf_3m > 10,
        "outperforming_spy": spy_relative is not None and spy_relative > 0,
        "healthy_sma50_distance": distance_sma50 is not None and -5 <= distance_sma50 <= 35,
        "above_sma200_meaningful": distance_sma200 is not None and distance_sma200 > 0,
    }

    passed = sum(1 for value in checks.values() if value)
    score = int(round((passed / len(checks)) * 100, 0))

    if score >= 80:
        status = "Stage 2 stark"
    elif score >= 60:
        status = "Stage 2 möglich"
    elif score >= 40:
        status = "Trend gemischt"
    else:
        status = "kein Stage-2-Trend"

    return score, status


def score_stock(perf_2m, spy_relative, qqq_relative, stage2_score, quality_pass, setup_type, close, market_cap_m, dollar_volume_m):
    score = 0

    if quality_pass:
        score += 15

    if perf_2m is not None and perf_2m >= 15:
        score += 20

    if perf_2m is not None and perf_2m >= 25:
        score += 10

    if spy_relative is not None and spy_relative > 0:
        score += 10

    if qqq_relative is not None and qqq_relative > 0:
        score += 7

    if stage2_score >= 80:
        score += 18
    elif stage2_score >= 60:
        score += 10

    if market_cap_m is not None and market_cap_m >= 1000:
        score += 5

    if dollar_volume_m is not None and dollar_volume_m >= 50:
        score += 5

    if close is not None and close >= 10:
        score += 5

    if setup_type == "Pre-Earnings":
        score += 5

    score = min(score, 100)

    if score >= 80 and quality_pass:
        rating = "A"
    elif score >= 65 and quality_pass:
        rating = "B"
    elif score >= 50 and quality_pass:
        rating = "C"
    elif not quality_pass:
        rating = "Ignore"
    else:
        rating = "Watch"

    return score, rating


def classify_stock(perf_2m, min_performance, score, rating, quality_pass, quality_reason, setup_type, stage2_score):
    if not quality_pass:
        return (
            "Ignore",
            f"Qualitätsfilter nicht erfüllt: {quality_reason}",
            "Ignorieren",
        )

    if perf_2m is None:
        return (
            "Keine Daten",
            "Keine verwertbare Performance aus TradingView.",
            "Ignorieren",
        )

    if setup_type == "Pre-Earnings":
        if perf_2m >= min_performance and score >= 80 and stage2_score >= 70:
            return (
                "A-Setup",
                "Pre-Earnings Runner: starkes Momentum vor den Zahlen, gute Trendqualität und ausreichende Liquidität.",
                "Detailanalyse prüfen",
            )

        if perf_2m >= min_performance and score >= 65:
            return (
                "B-Setup",
                "Pre-Earnings Momentum vorhanden. Qualität prüfen, aber grundsätzlich interessant.",
                "Watchlist / Detailanalyse",
            )

    if setup_type == "Post-Earnings":
        if perf_2m >= min_performance and score >= 75:
            return (
                "Post-Earnings Winner",
                "Starke Reaktion rund um bereits gemeldete Zahlen. Kann ein Anschluss-Setup sein.",
                "Nach Zahlenreaktion prüfen",
            )

        if perf_2m >= min_performance and score >= 60:
            return (
                "B-Setup",
                "Post-Earnings Momentum vorhanden, aber nicht perfekt.",
                "Watchlist",
            )

    if perf_2m >= min_performance:
        return (
            "Treffer",
            "Momentum-Filter erfüllt, aber Setup-Qualität ist nicht stark genug für A/B.",
            "Prüfen",
        )

    if perf_2m >= min_performance - 5:
        return (
            "Watchlist",
            "Knapp unter Momentum-Filter. Beobachten, aber noch kein Treffer.",
            "Watchlist",
        )

    if perf_2m >= 0:
        return (
            "Unter Filter",
            "Positives, aber zu schwaches Momentum.",
            "Ignorieren",
        )

    return (
        "Schwach",
        "Negatives Momentum. Für diesen Ansatz uninteressant.",
        "Ignorieren",
    )


def build_result_row(candidate, min_performance, spy_perf, qqq_perf, quality_params):
    symbol = normalize_symbol(candidate.get("symbol"))
    company = candidate.get("company") or COMPANY_FALLBACK_MAP.get(symbol) or symbol
    exchange = normalize_exchange(candidate.get("exchange") or EXCHANGE_FALLBACK_MAP.get(symbol, "UNKNOWN"))

    close = safe_number(candidate.get("current_close"))
    volume = safe_number(candidate.get("volume"))
    market_cap = safe_number(candidate.get("market_cap"))

    perf_1m = safe_number(candidate.get("performance_1m_pct"))
    perf_3m = safe_number(candidate.get("performance_3m_pct"))
    perf_6m = safe_number(candidate.get("performance_6m_pct"))
    perf_2m = estimate_2m_from_1m_3m(perf_1m, perf_3m)

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

    quality_pass, quality_reason, market_cap_m, dollar_volume_m = quality_check(
        candidate=candidate,
        min_price=quality_params["min_price"],
        min_market_cap_m=quality_params["min_market_cap_m"],
        min_volume=quality_params["min_volume"],
        min_dollar_volume_m=quality_params["min_dollar_volume_m"],
        allowed_exchanges=quality_params["allowed_exchanges"],
        exclude_otc=quality_params["exclude_otc"],
    )

    stage2_score, stage2_status = calculate_stage2_score(
        close=close,
        sma50=sma50,
        sma200=sma200,
        perf_3m=perf_3m,
        perf_6m=perf_6m,
        spy_relative=spy_relative,
        distance_sma50=distance_sma50,
        distance_sma200=distance_sma200,
    )

    setup_type = candidate.get("setup_type") or "n/a"

    score, rating = score_stock(
        perf_2m=perf_2m,
        spy_relative=spy_relative,
        qqq_relative=qqq_relative,
        stage2_score=stage2_score,
        quality_pass=quality_pass,
        setup_type=setup_type,
        close=close,
        market_cap_m=market_cap_m,
        dollar_volume_m=dollar_volume_m,
    )

    status, interpretation, action = classify_stock(
        perf_2m=perf_2m,
        min_performance=min_performance,
        score=score,
        rating=rating,
        quality_pass=quality_pass,
        quality_reason=quality_reason,
        setup_type=setup_type,
        stage2_score=stage2_score,
    )

    return {
        "symbol": symbol,
        "company": company,
        "wkn": WKN_MAP.get(symbol, "n/a"),
        "isin": "n/a",
        "exchange": exchange,
        "sector": candidate.get("sector", "n/a"),
        "industry": candidate.get("industry", "n/a"),
        "setup_type": setup_type,
        "earnings_date": candidate.get("earnings_date") or "n/a",
        "calendar_source": candidate.get("calendar_source") or "n/a",
        "current_close": close,
        "market_cap": market_cap,
        "market_cap_m": round(market_cap_m, 2) if market_cap_m is not None else None,
        "volume": volume,
        "dollar_volume_m": round(dollar_volume_m, 2) if dollar_volume_m is not None else None,
        "performance_1m_pct": round(perf_1m, 2) if perf_1m is not None else None,
        "performance_3m_pct": round(perf_3m, 2) if perf_3m is not None else None,
        "performance_6m_pct": round(perf_6m, 2) if perf_6m is not None else None,
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
        "quality_pass": quality_pass,
        "quality_reason": quality_reason,
        "interpretation": interpretation,
        "action": action,
        "chart_url": tradingview_url(symbol, exchange),
        "data_source": "TradingView Screener",
    }


def analyze_single_symbol(symbol, min_performance_2m=15.0):
    symbol = normalize_symbol(symbol)

    if not symbol:
        return None

    tv_df, error = get_tradingview_universe(limit=12000)

    if error or tv_df.empty:
        return None

    tv_info = build_tv_info_map(tv_df)

    if symbol not in tv_info:
        return None

    market = calculate_market_proxy()

    quality_params = {
        "min_price": 0,
        "min_market_cap_m": 0,
        "min_volume": 0,
        "min_dollar_volume_m": 0,
        "allowed_exchanges": [],
        "exclude_otc": False,
    }

    candidate = dict(tv_info[symbol])
    candidate["earnings_date"] = "nicht geprüft"
    candidate["calendar_source"] = "Manuelle TradingView-Prüfung"
    candidate["setup_type"] = "Manuell"

    row = build_result_row(
        candidate=candidate,
        min_performance=min_performance_2m,
        spy_perf=market.get("spy_perf_2m"),
        qqq_perf=market.get("qqq_perf_2m"),
        quality_params=quality_params,
    )

    return pd.DataFrame([row], columns=COLUMNS)


def run_screen(
    lookback_days=7,
    forward_days=14,
    min_performance_2m=15.0,
    tradingview_limit=8000,
    min_price=10.0,
    min_market_cap_m=500.0,
    min_volume=500_000,
    min_dollar_volume_m=20.0,
    allowed_exchanges=None,
    exclude_otc=True,
    apply_quality_filter=True,
    setup_filter="Alle",
):
    if allowed_exchanges is None:
        allowed_exchanges = ["NASDAQ", "NYSE", "AMEX"]

    today = date.today()
    start_date = today - timedelta(days=lookback_days)
    end_date = today + timedelta(days=forward_days)

    tv_candidates, tv_info, tv_error = get_tradingview_earnings_candidates(
        start_date=start_date,
        end_date=end_date,
        limit=tradingview_limit,
    )

    api_candidates, fmp_earnings, finnhub_earnings = get_api_candidates(
        start_date=start_date,
        end_date=end_date,
        tv_info=tv_info,
    )

    candidates = merge_candidates([tv_candidates, api_candidates])

    market = calculate_market_proxy()

    quality_params = {
        "min_price": min_price,
        "min_market_cap_m": min_market_cap_m,
        "min_volume": min_volume,
        "min_dollar_volume_m": min_dollar_volume_m,
        "allowed_exchanges": allowed_exchanges,
        "exclude_otc": exclude_otc,
    }

    rows = []

    for candidate in candidates:
        row = build_result_row(
            candidate=candidate,
            min_performance=min_performance_2m,
            spy_perf=market.get("spy_perf_2m"),
            qqq_perf=market.get("qqq_perf_2m"),
            quality_params=quality_params,
        )

        if row["performance_2m_proxy_pct"] is None:
            continue

        if setup_filter == "Nur Pre-Earnings" and row["setup_type"] != "Pre-Earnings":
            continue

        if setup_filter == "Nur Post-Earnings" and row["setup_type"] != "Post-Earnings":
            continue

        if apply_quality_filter and not row["quality_pass"]:
            continue

        rows.append(row)

    all_df = pd.DataFrame(rows, columns=COLUMNS)

    if not all_df.empty:
        all_df = all_df.sort_values(
            by=["score", "performance_2m_proxy_pct", "stage2_score"],
            ascending=[False, False, False],
        )

    hits_df = all_df[
        all_df["performance_2m_proxy_pct"] >= min_performance_2m
    ].copy()

    if not hits_df.empty:
        hits_df = hits_df.sort_values(
            by=["score", "performance_2m_proxy_pct", "stage2_score"],
            ascending=[False, False, False],
        )

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
        "hits": len(hits_df),
        "start_date": str(start_date),
        "end_date": str(end_date),
        "min_performance_2m": min_performance_2m,
        "best_symbol": best_symbol,
        "best_company": best_company,
        "best_performance": best_performance,
        "spy_perf_2m": market.get("spy_perf_2m"),
        "qqq_perf_2m": market.get("qqq_perf_2m"),
        "min_price": min_price,
        "min_market_cap_m": min_market_cap_m,
        "min_volume": min_volume,
        "min_dollar_volume_m": min_dollar_volume_m,
        "allowed_exchanges": allowed_exchanges,
        "exclude_otc": exclude_otc,
        "apply_quality_filter": apply_quality_filter,
        "setup_filter": setup_filter,
    }

    return hits_df, all_df, stats
