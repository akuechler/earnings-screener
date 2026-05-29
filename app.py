import json

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from screener import analyze_single_symbol, run_screen


st.set_page_config(
    page_title="Earnings Momentum Screener",
    layout="wide",
)

st.title("Earnings Momentum Screener")
st.caption(
    "TradingView-basierter Earnings-Momentum-Screener. "
    "TradingView ist die Hauptquelle. FMP/Finnhub ergänzen Earnings-Termine."
)

st.sidebar.header("Steuerung")

lookback_days = st.sidebar.slider(
    "Rückblick in Tagen",
    min_value=0,
    max_value=21,
    value=7,
    step=1,
)

forward_days = st.sidebar.slider(
    "Ausblick in Tagen",
    min_value=3,
    max_value=30,
    value=14,
    step=1,
)

min_performance = st.sidebar.slider(
    "Momentum-Filter in %",
    min_value=0.0,
    max_value=50.0,
    value=15.0,
    step=1.0,
)

tradingview_limit = st.sidebar.slider(
    "TradingView Universe-Limit",
    min_value=1000,
    max_value=20000,
    value=8000,
    step=1000,
    help="Höher = mehr Aktienuniversum. TradingView liefert Performance-Daten direkt.",
)

show_chart_previews = st.sidebar.checkbox(
    "Chart-Vorschau anzeigen",
    value=True,
    help="Zeigt pro Aktie eine aufklappbare TradingView-Candlestick-Vorschau.",
)

max_cards = st.sidebar.slider(
    "Maximale Karten anzeigen",
    min_value=5,
    max_value=50,
    value=20,
    step=5,
    help="Mehr Karten bedeuten mehr Chart-Widgets und längere Ladezeit.",
)

run_now = st.sidebar.button("Screener jetzt ausführen")

st.sidebar.divider()

manual_symbol = st.sidebar.text_input(
    "Ticker manuell prüfen",
    value="DELL",
)

manual_check = st.sidebar.button("Ticker prüfen")


def format_percent(value):
    if value is None or pd.isna(value):
        return "n/a"

    try:
        return f"{float(value):.2f} %".replace(".", ",")
    except Exception:
        return "n/a"


def format_currency(value):
    if value is None or pd.isna(value):
        return "n/a"

    try:
        return f"{float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "n/a"


def format_date_de(value):
    if value is None or value == "" or str(value).lower() in ["n/a", "nan", "nat"]:
        return "n/a"

    if str(value).lower() in ["nicht geprüft"]:
        return "nicht geprüft"

    try:
        parsed = pd.to_datetime(value, errors="coerce")

        if pd.isna(parsed):
            return str(value)

        return parsed.strftime("%d.%m.%Y")
    except Exception:
        return str(value)


def status_badge(status):
    if status == "Treffer":
        return "🟢 Treffer"
    if status == "Knapp darunter":
        return "🟡 Knapp darunter"
    if status == "Schwach":
        return "🔴 Schwach"
    if status == "Keine Daten":
        return "⚪ Keine Daten"

    return "⚪ Unter Filter"


def rating_badge(rating):
    if rating == "A":
        return "A-Setup"
    if rating == "B":
        return "B-Setup"
    if rating == "C":
        return "C-Setup"

    return "Watch"


def normalize_exchange_for_tradingview(exchange):
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


def make_tradingview_symbol(ticker, exchange):
    ticker = str(ticker).upper().strip()
    tv_exchange = normalize_exchange_for_tradingview(exchange)

    return f"{tv_exchange}:{ticker}"


def show_tradingview_preview(ticker, exchange):
    tv_symbol = make_tradingview_symbol(ticker, exchange)

    widget_config = {
        "autosize": True,
        "symbol": tv_symbol,
        "interval": "D",
        "timezone": "Europe/Berlin",
        "theme": "light",
        "style": "1",
        "locale": "de_DE",
        "range": "3M",
        "backgroundColor": "#ffffff",
        "gridColor": "rgba(46, 46, 46, 0.06)",
        "hide_top_toolbar": True,
        "hide_legend": False,
        "save_image": False,
        "calendar": False,
        "hide_volume": False,
        "support_host": "https://www.tradingview.com",
    }

    html = f"""
    <div class="tradingview-widget-container" style="height:420px;width:100%;">
      <div class="tradingview-widget-container__widget" style="height:420px;width:100%;"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js" async>
      {json.dumps(widget_config)}
      </script>
    </div>
    """

    components.html(html, height=435, scrolling=False)


def prepare_display_df(df):
    if df is None or df.empty:
        return pd.DataFrame()

    display = df.copy()

    display["Datum"] = display["earnings_date"].apply(format_date_de)
    display["Kurs"] = display["current_close"].apply(format_currency)
    display["1M"] = display["performance_1m_pct"].apply(format_percent)
    display["3M"] = display["performance_3m_pct"].apply(format_percent)
    display["2M Proxy"] = display["performance_2m_proxy_pct"].apply(format_percent)
    display["Relativ zu SPY"] = display["spy_relative_proxy_pct"].apply(format_percent)
    display["Relativ zu QQQ"] = display["qqq_relative_proxy_pct"].apply(format_percent)
    display["Abstand 50-Tage-Linie"] = display["distance_sma_50_pct"].apply(format_percent)
    display["Abstand 200-Tage-Linie"] = display["distance_sma_200_pct"].apply(format_percent)
    display["Statusanzeige"] = display["status"].apply(status_badge)
    display["Ratinganzeige"] = display["rating"].apply(rating_badge)

    return display


def show_market_regime(stats):
    market = stats.get("market_regime", {})

    regime = market.get("regime", "unbekannt")
    interpretation = market.get("interpretation", "")

    if regime == "grün":
        st.success(f"Marktampel: GRÜN — {interpretation}")
    elif regime == "rot":
        st.error(f"Marktampel: ROT — {interpretation}")
    elif regime == "neutral":
        st.warning(f"Marktampel: NEUTRAL — {interpretation}")
    else:
        st.info(f"Marktampel: UNBEKANNT — {interpretation}")

    col1, col2 = st.columns(2)

    spy_perf = market.get("spy_perf_2m")
    qqq_perf = market.get("qqq_perf_2m")

    col1.metric("SPY 2M Proxy", format_percent(spy_perf))
    col2.metric("QQQ 2M Proxy", format_percent(qqq_perf))


def show_candidate_cards(df, title, empty_message, limit=20, show_charts=True):
    st.subheader(title)

    if df is None or df.empty:
        st.warning(empty_message)
        return

    display = prepare_display_df(df)

    for _, row in display.head(limit).iterrows():
        company = row.get("company", "n/a")
        ticker = row.get("symbol", "n/a")
        wkn = row.get("wkn", "n/a")
        exchange = row.get("exchange", "n/a")
        chart_url = row.get("chart_url", "")
        interpretation = row.get("interpretation", "")
        action = row.get("action", "")
        source = row.get("calendar_source", "n/a")
        data_source = row.get("data_source", "n/a")

        with st.container(border=True):
            header_left, header_right = st.columns([4, 1])

            with header_left:
                st.markdown(f"### {company} ({ticker})")
                st.caption(
                    f"WKN: {wkn} · Börse: {exchange} · Earnings: {row['Datum']} · Quelle: {source}"
                )

            with header_right:
                if chart_url:
                    st.link_button("Chart öffnen", chart_url, use_container_width=True)

            k1, k2, k3, k4, k5 = st.columns(5)

            k1.metric("Aktueller Kurs", row["Kurs"])
            k2.metric("2M Proxy", row["2M Proxy"])
            k3.metric("Abstand 50-Tage-Linie", row["Abstand 50-Tage-Linie"])
            k4.metric("Abstand 200-Tage-Linie", row["Abstand 200-Tage-L
