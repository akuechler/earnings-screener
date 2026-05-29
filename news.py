import os
from datetime import date, timedelta
from urllib.parse import quote_plus

import requests
import streamlit as st


REQUEST_TIMEOUT = 10


def get_secret(name):
    value = os.getenv(name)

    if value:
        return value

    try:
        return st.secrets[name]
    except Exception:
        return None


FINNHUB_API_KEY = get_secret("FINNHUB_API_KEY")
FMP_API_KEY = get_secret("FMP_API_KEY")


def _safe_text(value):
    if value is None:
        return ""

    return str(value).strip()


def _safe_date_text(value):
    if value is None:
        return ""

    try:
        if isinstance(value, (int, float)):
            if value > 10_000_000_000:
                return date.fromtimestamp(value / 1000).isoformat()

            if value > 1_000_000_000:
                return date.fromtimestamp(value).isoformat()
    except Exception:
        pass

    return str(value).strip()


def google_news_de_url(symbol, company):
    symbol = _safe_text(symbol).upper()
    company = _safe_text(company)

    query = f"{symbol} Aktie {company}".strip()

    return (
        "https://news.google.com/search?q="
        + quote_plus(query)
        + "&hl=de&gl=DE&ceid=DE:de"
    )


def google_news_en_url(symbol, company):
    symbol = _safe_text(symbol).upper()
    company = _safe_text(company)

    query = f"{symbol} stock {company}".strip()

    return (
        "https://news.google.com/search?q="
        + quote_plus(query)
        + "&hl=en-US&gl=US&ceid=US:en"
    )


def _normalize_news_item(item, source_hint):
    title = (
        item.get("headline")
        or item.get("title")
        or item.get("site")
        or item.get("text")
        or ""
    )

    url = (
        item.get("url")
        or item.get("link")
        or ""
    )

    source = (
        item.get("source")
        or item.get("site")
        or item.get("publisher")
        or source_hint
    )

    published = (
        item.get("datetime")
        or item.get("publishedDate")
        or item.get("date")
        or item.get("published")
        or ""
    )

    summary = (
        item.get("summary")
        or item.get("text")
        or item.get("snippet")
        or ""
    )

    title = _safe_text(title)
    url = _safe_text(url)
    source = _safe_text(source)
    published = _safe_date_text(published)
    summary = _safe_text(summary)

    if not title:
        return None

    return {
        "title": title,
        "url": url,
        "source": source,
        "published": published,
        "summary": summary,
    }


@st.cache_data(ttl=1800, show_spinner=False)
def get_finnhub_company_news(symbol, days_back=14, limit=5):
    symbol = _safe_text(symbol).upper()

    if not symbol or not FINNHUB_API_KEY:
        return []

    end_date = date.today()
    start_date = end_date - timedelta(days=days_back)

    url = (
        "https://finnhub.io/api/v1/company-news"
        f"?symbol={quote_plus(symbol)}"
        f"&from={start_date.isoformat()}"
        f"&to={end_date.isoformat()}"
        f"&token={FINNHUB_API_KEY}"
    )

    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
    except Exception:
        return []

    if not isinstance(data, list):
        return []

    news = []

    for item in data:
        if not isinstance(item, dict):
            continue

        normalized = _normalize_news_item(item, "Finnhub")

        if normalized:
            news.append(normalized)

        if len(news) >= limit:
            break

    return news


@st.cache_data(ttl=1800, show_spinner=False)
def get_fmp_stock_news(symbol, limit=5):
    symbol = _safe_text(symbol).upper()

    if not symbol or not FMP_API_KEY:
        return []

    url = (
        "https://financialmodelingprep.com/stable/news/stock"
        f"?symbols={quote_plus(symbol)}"
        f"&apikey={FMP_API_KEY}"
    )

    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
    except Exception:
        return []

    if not isinstance(data, list):
        return []

    news = []

    for item in data:
        if not isinstance(item, dict):
            continue

        normalized = _normalize_news_item(item, "FMP")

        if normalized:
            news.append(normalized)

        if len(news) >= limit:
            break

    return news


@st.cache_data(ttl=1800, show_spinner=False)
def get_company_news(symbol, limit=3):
    symbol = _safe_text(symbol).upper()

    if not symbol:
        return []

    combined = []

    for item in get_finnhub_company_news(symbol, days_back=14, limit=limit):
        combined.append(item)

    if len(combined) < limit:
        for item in get_fmp_stock_news(symbol, limit=limit):
            combined.append(item)

    deduped = []
    seen = set()

    for item in combined:
        key = (item.get("title") or "").lower().strip()

        if not key or key in seen:
            continue

        seen.add(key)
        deduped.append(item)

        if len(deduped) >= limit:
            break

    return deduped
