from html import escape

import pandas as pd
import streamlit as st

from news import get_company_news, google_news_de_url, google_news_en_url
from screener import analyze_single_symbol, run_screen


st.set_page_config(
    page_title="Earnings Momentum Screener",
    layout="wide",
)


st.markdown(
    """
    <style>
        .stApp {
            background: #0B0F17;
            color: #F8FAFC;
        }

        [data-testid="stSidebar"] {
            background: #111827;
            border-right: 1px solid rgba(255,255,255,0.14);
        }

        [data-testid="stSidebar"] * {
            color: #F8FAFC !important;
            opacity: 1 !important;
        }

        [data-testid="stSidebar"] input {
            background: #F8FAFC !important;
            color: #111827 !important;
            border: 1px solid rgba(255,255,255,0.28) !important;
        }

        .block-container {
            padding-top: 1.7rem;
            padding-left: 2.1rem;
            padding-right: 2.1rem;
            max-width: 1620px;
        }

        h1, h2, h3, h4 {
            color: #FFFFFF !important;
            letter-spacing: -0.02em;
        }

        label,
        [data-testid="stWidgetLabel"],
        [data-testid="stWidgetLabel"] *,
        [data-testid="stMarkdownContainer"] p {
            color: #F8FAFC !important;
            opacity: 1 !important;
            font-weight: 750 !important;
        }

        input,
        textarea {
            color: #111827 !important;
            background: #F8FAFC !important;
        }

        [data-baseweb="select"] > div {
            background: #F8FAFC !important;
            border: 1px solid rgba(15,23,42,0.35) !important;
            border-radius: 10px !important;
            min-height: 44px !important;
        }

        [data-baseweb="select"] input,
        [data-baseweb="select"] span,
        [data-baseweb="select"] div {
            color: #111827 !important;
            opacity: 1 !important;
            font-weight: 750 !important;
        }

        [data-baseweb="popover"] {
            z-index: 999999 !important;
        }

        [role="listbox"] {
            background: #F8FAFC !important;
            border: 1px solid rgba(15,23,42,0.22) !important;
        }

        [role="option"],
        [role="option"] * {
            background: #F8FAFC !important;
            color: #111827 !important;
            opacity: 1 !important;
            font-weight: 750 !important;
        }

        [role="option"]:hover,
        [role="option"]:hover * {
            background: #DBEAFE !important;
            color: #111827 !important;
        }

        .main-header {
            padding: 20px 24px;
            border-radius: 22px;
            background: linear-gradient(135deg, #1E293B 0%, #172033 100%);
            border: 1px solid rgba(255,255,255,0.18);
            box-shadow: 0 12px 30px rgba(0,0,0,0.32);
            margin-bottom: 22px;
        }

        .main-title {
            font-size: 36px;
            font-weight: 900;
            line-height: 1.08;
            margin-bottom: 7px;
            color: #FFFFFF;
        }

        .main-subtitle {
            font-size: 14px;
            color: #E2E8F0;
            font-weight: 650;
        }

        .panel {
            background: #1B263A;
            border: 1px solid rgba(255,255,255,0.22);
            border-radius: 20px;
            padding: 18px 20px;
            margin-bottom: 18px;
            box-shadow: 0 10px 24px rgba(0,0,0,0.24);
        }

        .panel-title {
            font-size: 22px;
            font-weight: 900;
            margin-bottom: 8px;
            color: #FFFFFF;
        }

        .panel-text {
            font-size: 14px;
            color: #F8FAFC;
            line-height: 1.45;
            font-weight: 650;
        }

        .kpi-card {
            background: #182235;
            border: 1px solid rgba(255,255,255,0.24);
            border-radius: 16px;
            padding: 13px 14px;
            min-height: 82px;
            box-shadow: 0 6px 16px rgba(0,0,0,0.20);
            margin-bottom: 12px;
        }

        .kpi-label {
            color: #FFFFFF;
            font-size: 12px;
            font-weight: 900;
            margin-bottom: 8px;
            white-space: normal;
        }

        .kpi-value {
            color: #FFFFFF;
            font-size: 26px;
            font-weight: 950;
            line-height: 1.05;
            word-break: break-word;
        }

        .kpi-sub {
            display: inline-flex;
            margin-top: 7px;
            border-radius: 999px;
            padding: 4px 8px;
            font-size: 12px;
            font-weight: 850;
            background: rgba(37,99,235,0.24);
            color: #DBEAFE;
            border: 1px solid rgba(37,99,235,0.55);
        }

        .kpi-green {
            background: rgba(34,197,94,0.20);
            color: #BBF7D0;
            border-color: rgba(34,197,94,0.55);
        }

        .kpi-yellow {
            background: rgba(245,158,11,0.20);
            color: #FDE68A;
            border-color: rgba(245,158,11,0.55);
        }

        .top-candidate {
            background: linear-gradient(135deg, #102A43 0%, #162032 100%);
            border: 1px solid rgba(34,197,94,0.42);
            border-radius: 20px;
            padding: 18px 20px;
            margin-bottom: 18px;
            box-shadow: 0 10px 24px rgba(0,0,0,0.24);
        }

        .top-candidate-label {
            color: #BBF7D0;
            font-size: 12px;
            font-weight: 900;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 8px;
        }

        .top-candidate-title {
            font-size: 28px;
            font-weight: 950;
            color: #FFFFFF;
            margin-bottom: 8px;
            line-height: 1.1;
        }

        .top-candidate-meta {
            color: #E2E8F0;
            font-size: 13px;
            font-weight: 700;
            line-height: 1.45;
        }

        .control-panel {
            background: #1B263A;
            border: 1px solid rgba(255,255,255,0.22);
            border-radius: 20px;
            padding: 18px 20px;
            margin-top: 6px;
            margin-bottom: 20px;
            box-shadow: 0 10px 24px rgba(0,0,0,0.24);
        }

        .control-title {
            font-size: 22px;
            font-weight: 950;
            color: #FFFFFF;
            margin-bottom: 6px;
        }

        .control-text {
            color: #E2E8F0;
            font-size: 13px;
            font-weight: 650;
            margin-bottom: 14px;
        }

        .filter-chip-line {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 8px;
            margin-bottom: 8px;
        }

        .filter-chip {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 6px 11px;
            font-size: 12px;
            font-weight: 850;
            background: rgba(37,99,235,0.28);
            border: 1px solid rgba(37,99,235,0.68);
            color: #DBEAFE;
        }

        .stock-header {
            background: #162032;
            border: 1px solid rgba(255,255,255,0.18);
            border-radius: 22px;
            padding: 18px;
            margin-bottom: 14px;
            box-shadow: 0 12px 28px rgba(0,0,0,0.30);
        }

        .stock-header-hit {
            border-color: rgba(34,197,94,0.78);
            box-shadow: 0 0 0 1px rgba(34,197,94,0.24), 0 12px 28px rgba(0,0,0,0.30);
        }

        .stock-header-watch {
            border-color: rgba(245,158,11,0.60);
        }

        .stock-header-ignore {
            border-color: rgba(239,68,68,0.55);
            opacity: 0.88;
        }

        .stock-title {
            font-size: 22px;
            font-weight: 900;
            color: #FFFFFF;
            margin-bottom: 4px;
        }

        .stock-meta {
            color: #F1F5F9;
            font-size: 12px;
            margin-bottom: 0;
            font-weight: 750;
        }

        .metric-box {
            background: #101827;
            border: 1px solid rgba(255,255,255,0.26);
            border-radius: 15px;
            padding: 10px 11px;
            min-height: 72px;
        }

        .metric-label {
            font-size: 11px;
            color: #FFFFFF;
            margin-bottom: 5px;
            white-space: normal;
            font-weight: 900;
        }

        .metric-value {
            font-size: 20px;
            line-height: 1.15;
            font-weight: 950;
            color: #FFFFFF;
            white-space: normal;
        }

        .metric-value-small {
            font-size: 17px;
            line-height: 1.15;
            font-weight: 950;
            color: #FFFFFF;
            white-space: normal;
        }

        .positive {
            color: #22C55E !important;
        }

        .negative {
            color: #F87171 !important;
        }

        .neutral {
            color: #FBBF24 !important;
        }

        .muted {
            color: #F8FAFC !important;
        }

        .badge-row {
            display: flex;
            flex-wrap: wrap;
            gap: 7px;
            margin-top: 11px;
            margin-bottom: 8px;
        }

        .badge {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 5px 10px;
            font-size: 12px;
            font-weight: 850;
            border: 1px solid rgba(255,255,255,0.22);
            background: #101827;
            color: #F8FAFC;
        }

        .badge-green {
            background: rgba(34,197,94,0.22);
            border-color: rgba(34,197,94,0.62);
            color: #BBF7D0;
        }

        .badge-yellow {
            background: rgba(245,158,11,0.22);
            border-color: rgba(245,158,11,0.62);
            color: #FDE68A;
        }

        .badge-red {
            background: rgba(239,68,68,0.22);
            border-color: rgba(239,68,68,0.62);
            color: #FECACA;
        }

        .badge-blue {
            background: rgba(59,130,246,0.22);
            border-color: rgba(59,130,246,0.62);
            color: #BFDBFE;
        }

        .info-line {
            color: #F1F5F9;
            font-size: 13px;
            line-height: 1.45;
            margin-top: 8px;
            font-weight: 650;
        }

        .chart-wrap {
            background: #FFFFFF;
            border: 1px solid rgba(255,255,255,0.18);
            border-radius: 16px;
            overflow: hidden;
            padding: 8px;
            margin-top: 2px;
        }

        .chart-wrap img {
            width: 100%;
            max-width: 500px;
            height: auto;
            display: block;
            border-radius: 10px;
        }

        .chart-caption {
            font-size: 11px;
            color: #334155;
            margin-top: 6px;
            font-weight: 800;
        }

        .news-box {
            background: #0F1726;
            border: 1px solid rgba(255,255,255,0.20);
            border-radius: 16px;
            padding: 14px 16px;
            margin-top: 12px;
            margin-bottom: 4px;
        }

        .news-title {
            font-size: 15px;
            font-weight: 950;
            color: #FFFFFF;
            margin-bottom: 10px;
        }

        .news-item {
            border-top: 1px solid rgba(255,255,255,0.11);
            padding-top: 9px;
            margin-top: 9px;
        }

        .news-headline {
            font-size: 13px;
            font-weight: 850;
            color: #F8FAFC;
            line-height: 1.35;
        }

        .news-headline a {
            color: #DBEAFE;
            text-decoration: none;
        }

        .news-headline a:hover {
            text-decoration: underline;
        }

        .news-meta {
            font-size: 11px;
            color: #CBD5E1;
            font-weight: 750;
            margin-top: 4px;
        }

        .news-summary {
            font-size: 12px;
            color: #E2E8F0;
            line-height: 1.35;
            margin-top: 5px;
        }

        .news-actions {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 10px;
            margin-top: 12px;
        }

        .news-button {
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 36px;
            border-radius: 12px;
            background: #2563EB;
            color: #FFFFFF !important;
            text-decoration: none !important;
            font-size: 13px;
            font-weight: 900;
            border: 1px solid rgba(255,255,255,0.22);
            box-shadow: 0 6px 16px rgba(37,99,235,0.22);
        }

        .news-button:hover {
            background: #1D4ED8;
        }

        .stButton > button,
        .stLinkButton > a {
            background: #2563EB !important;
            color: #FFFFFF !important;
            border: 1px solid rgba(255,255,255,0.24) !important;
            border-radius: 12px !important;
            font-weight: 850 !important;
            box-shadow: 0 6px 16px rgba(37,99,235,0.22);
        }

        .stButton > button:hover,
        .stLinkButton > a:hover {
            background: #1D4ED8 !important;
            color: #FFFFFF !important;
            border-color: rgba(255,255,255,0.34) !important;
        }

        .stAlert {
            border-radius: 16px;
            color: #F8FAFC !important;
        }

        .stAlert * {
            color: inherit !important;
        }

        [data-testid="stDataFrame"] {
            background: #182235;
            border-radius: 16px;
            overflow: hidden;
        }

        hr {
            border-color: rgba(255,255,255,0.12);
        }
    </style>
    """,
    unsafe_allow_html=True,
)


st.markdown(
    """
    <div class="main-header">
        <div class="main-title">Earnings Momentum Screener von Andreas</div>
        <div class="main-subtitle">
            Analyst Cockpit · Qualitätsfilter · Pre-/Post-Earnings · Momentum · 50-/200-Tage-Linie · News · Chartvorschau
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


if "sort_key" not in st.session_state:
    st.session_state.sort_key = "score"

if "hits_df" not in st.session_state:
    st.session_state.hits_df = None

if "all_df" not in st.session_state:
    st.session_state.all_df = None

if "stats" not in st.session_state:
    st.session_state.stats = None

if "has_results" not in st.session_state:
    st.session_state.has_results = False


st.sidebar.header("Screening")

lookback_days = st.sidebar.slider(
    "Rückblick in Kalendertagen",
    min_value=0,
    max_value=21,
    value=0,
    step=1,
)

forward_days = st.sidebar.slider(
    "Ausblick in Kalendertagen",
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
    value=10000,
    step=1000,
)

setup_filter = st.sidebar.selectbox(
    "Earnings-Setup",
    options=["Alle", "Nur Pre-Earnings", "Nur Post-Earnings"],
    index=0,
)

st.sidebar.divider()
st.sidebar.header("Qualitätsfilter")

apply_quality_filter = st.sidebar.checkbox(
    "Qualitätsfilter aktiv",
    value=True,
)

allowed_exchanges = st.sidebar.multiselect(
    "Erlaubte Börsen",
    options=["NASDAQ", "NYSE", "AMEX", "OTC"],
    default=["NASDAQ", "NYSE", "AMEX"],
)

exclude_otc = st.sidebar.checkbox(
    "OTC ausschließen",
    value=True,
)

min_price = st.sidebar.slider(
    "Mindestkurs USD",
    min_value=0.0,
    max_value=100.0,
    value=10.0,
    step=1.0,
)

min_market_cap_m = st.sidebar.slider(
    "Mindest-Marktkapitalisierung Mio. USD",
    min_value=0.0,
    max_value=10000.0,
    value=500.0,
    step=100.0,
)

min_volume = st.sidebar.slider(
    "Mindestvolumen Aktien/Tag",
    min_value=0,
    max_value=5_000_000,
    value=500_000,
    step=100_000,
)

min_dollar_volume_m = st.sidebar.slider(
    "Mindest-Dollar-Volumen Mio. USD",
    min_value=0.0,
    max_value=500.0,
    value=20.0,
    step=5.0,
)

st.sidebar.divider()
st.sidebar.header("Darstellung")

show_chart_previews = st.sidebar.checkbox(
    "Chart-Vorschau anzeigen",
    value=True,
)

show_news = st.sidebar.checkbox(
    "News in Karten anzeigen",
    value=True,
)

max_news_per_stock = st.sidebar.slider(
    "News je Aktie",
    min_value=1,
    max_value=5,
    value=3,
    step=1,
)

max_cards = st.sidebar.slider(
    "Maximale Karten anzeigen",
    min_value=5,
    max_value=50,
    value=20,
    step=5,
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


def format_number(value):
    if value is None or pd.isna(value):
        return "n/a"

    try:
        return f"{float(value):,.0f}".replace(",", ".")
    except Exception:
        return "n/a"


def format_million(value):
    if value is None or pd.isna(value):
        return "n/a"

    try:
        return f"{float(value):,.1f} Mio.".replace(",", "X").replace(".", ",").replace("X", ".")
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


def format_news_date(value):
    if value is None or str(value).strip() == "":
        return "n/a"

    try:
        parsed = pd.to_datetime(value, errors="coerce")

        if pd.isna(parsed):
            return str(value)

        return parsed.strftime("%d.%m.%Y")
    except Exception:
        return str(value)


def numeric_class(value):
    try:
        number = float(value)

        if number > 0:
            return "positive"

        if number < 0:
            return "negative"

        return "muted"
    except Exception:
        return "muted"


def status_badge_class(status):
    if status in ["A-Setup", "Post-Earnings Winner"]:
        return "badge-green"

    if status in ["B-Setup", "Treffer", "Watchlist"]:
        return "badge-yellow"

    if status in ["Ignore", "Schwach"]:
        return "badge-red"

    return "badge-blue"


def rating_badge(rating):
    if rating == "A":
        return "A-Setup"

    if rating == "B":
        return "B-Setup"

    if rating == "C":
        return "C-Setup"

    if rating == "Ignore":
        return "Ignore"

    return "Watch"


def prepare_display_df(df):
    if df is None or df.empty:
        return pd.DataFrame()

    display = df.copy()

    display["Datum"] = display["earnings_date"].apply(format_date_de)
    display["Kurs"] = display["current_close"].apply(format_currency)
    display["Marktkapitalisierung"] = display["market_cap_m"].apply(format_million)
    display["Volumen"] = display["volume"].apply(format_number)
    display["Dollar-Volumen"] = display["dollar_volume_m"].apply(format_million)
    display["1M"] = display["performance_1m_pct"].apply(format_percent)
    display["3M"] = display["performance_3m_pct"].apply(format_percent)
    display["6M"] = display["performance_6m_pct"].apply(format_percent)
    display["2M Proxy"] = display["performance_2m_proxy_pct"].apply(format_percent)
    display["Relativ zu SPY"] = display["spy_relative_proxy_pct"].apply(format_percent)
    display["Relativ zu QQQ"] = display["qqq_relative_proxy_pct"].apply(format_percent)
    display["Abstand 50-Tage-Linie"] = display["distance_sma_50_pct"].apply(format_percent)
    display["Abstand 200-Tage-Linie"] = display["distance_sma_200_pct"].apply(format_percent)

    return display


def chart_preview_url(ticker):
    ticker = str(ticker).upper().strip()
    return f"https://finviz.com/chart.ashx?t={ticker}&ty=c&ta=1&p=d&s=l"


def show_chart_preview(ticker):
    ticker = str(ticker).upper().strip()
    url = chart_preview_url(ticker)

    st.markdown(
        f"""
        <div class="chart-wrap">
            <img src="{escape(url)}" alt="Chart {escape(ticker)}" />
            <div class="chart-caption">
                Chart-Vorschau {escape(ticker)} · Für Detailanalyse den TradingView-Link öffnen
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_box(label, value, css_class=""):
    return f"""
    <div class="metric-box">
        <div class="metric-label">{escape(str(label))}</div>
        <div class="metric-value {escape(str(css_class))}">{escape(str(value))}</div>
    </div>
    """


def metric_box_small(label, value, css_class=""):
    return f"""
    <div class="metric-box">
        <div class="metric-label">{escape(str(label))}</div>
        <div class="metric-value-small {escape(str(css_class))}">{escape(str(value))}</div>
    </div>
    """


def kpi_card(label, value, sub=None, color_class=""):
    sub_html = ""

    if sub:
        sub_html = f'<div class="kpi-sub {escape(str(color_class))}">{escape(str(sub))}</div>'

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{escape(str(label))}</div>
            <div class="kpi-value">{escape(str(value))}</div>
            {sub_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_news_block(symbol, company, limit):
    symbol = str(symbol).upper().strip()
    company = str(company).strip()

    news_items = get_company_news(symbol, limit=limit)
    de_url = google_news_de_url(symbol, company)
    en_url = google_news_en_url(symbol, company)

    items_html = ""

    if not news_items:
        items_html = """
            <div class="news-item">
                <div class="news-headline">Keine API-News gefunden.</div>
                <div class="news-meta">Nutze die externen News-Links für manuelle Prüfung.</div>
            </div>
        """
    else:
        for item in news_items[:limit]:
            title = escape(str(item.get("title", "Ohne Titel")))
            url = escape(str(item.get("url", "")))
            source = escape(str(item.get("source", "n/a")))
            published = escape(format_news_date(item.get("published")))
            summary = str(item.get("summary", "") or "")

            if url:
                headline_html = f'<a href="{url}" target="_blank" rel="noopener noreferrer">{title}</a>'
            else:
                headline_html = title

            summary_html = ""

            if summary:
                summary_short = summary[:220] + "..." if len(summary) > 220 else summary
                summary_html = f'<div class="news-summary">{escape(summary_short)}</div>'

            items_html += f"""
                <div class="news-item">
                    <div class="news-headline">{headline_html}</div>
                    <div class="news-meta">{source} · {published}</div>
                    {summary_html}
                </div>
            """

    st.markdown(
        f"""
        <div class="news-box">
            <div class="news-title">Aktuelle News</div>
            {items_html}
            <div class="news-actions">
                <a class="news-button" href="{escape(de_url)}" target="_blank" rel="noopener noreferrer">DE News öffnen</a>
                <a class="news-button" href="{escape(en_url)}" target="_blank" rel="noopener noreferrer">EN News öffnen</a>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def sort_dataframe(df, sort_key):
    if df is None or df.empty:
        return df

    sorted_df = df.copy()

    if sort_key == "score":
        return sorted_df.sort_values("score", ascending=False)

    if sort_key == "momentum":
        return sorted_df.sort_values("performance_2m_proxy_pct", ascending=False)

    if sort_key == "stage2":
        return sorted_df.sort_values("stage2_score", ascending=False)

    if sort_key == "market_cap":
        return sorted_df.sort_values("market_cap_m", ascending=False)

    if sort_key == "dollar_volume":
        return sorted_df.sort_values("dollar_volume_m", ascending=False)

    if sort_key == "earnings_date_asc":
        sorted_df["_sort_date"] = pd.to_datetime(sorted_df["earnings_date"], errors="coerce")
        return sorted_df.sort_values("_sort_date", ascending=True).drop(columns=["_sort_date"])

    if sort_key == "earnings_date_desc":
        sorted_df["_sort_date"] = pd.to_datetime(sorted_df["earnings_date"], errors="coerce")
        return sorted_df.sort_values("_sort_date", ascending=False).drop(columns=["_sort_date"])

    if sort_key == "distance_50":
        return sorted_df.sort_values("distance_sma_50_pct", ascending=False)

    if sort_key == "distance_200":
        return sorted_df.sort_values("distance_sma_200_pct", ascending=False)

    if sort_key == "ticker":
        return sorted_df.sort_values("symbol", ascending=True)

    return sorted_df.sort_values("score", ascending=False)


def show_screening_summary(stats, all_df, hits_df):
    start_date = format_date_de(stats.get("start_date"))
    end_date = format_date_de(stats.get("end_date"))

    if all_df is None or all_df.empty:
        a_setups = 0
        b_setups = 0
        pre_earnings = 0
        post_earnings = 0
        avg_momentum = None
    else:
        a_setups = int((all_df["status"] == "A-Setup").sum())
        b_setups = int((all_df["status"] == "B-Setup").sum())
        pre_earnings = int((all_df["setup_type"] == "Pre-Earnings").sum())
        post_earnings = int((all_df["setup_type"] == "Post-Earnings").sum())
        avg_momentum = all_df["performance_2m_proxy_pct"].mean()

    hits = 0 if hits_df is None else len(hits_df)

    st.markdown(
        f"""
        <div class="panel">
            <div class="panel-title">Screening-Übersicht</div>
            <div class="panel-text">
                Zeitraum: <b>{escape(start_date)}</b> bis <b>{escape(end_date)}</b><br>
                Qualitätsfilter: Kurs ≥ {escape(str(stats.get("min_price")))} USD ·
                Market Cap ≥ {escape(str(stats.get("min_market_cap_m")))} Mio. USD ·
                Volumen ≥ {escape(format_number(stats.get("min_volume")))} ·
                Dollar-Volumen ≥ {escape(str(stats.get("min_dollar_volume_m")))} Mio. USD
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4, c5, c6 = st.columns(6)

    with c1:
        kpi_card("Momentum-Treffer", hits, f"≥ {stats.get('min_performance_2m', 0):.0f} %", "kpi-green")

    with c2:
        kpi_card("A-Setups", a_setups, "höchste Qualität", "kpi-green")

    with c3:
        kpi_card("B-Setups", b_setups, "Watchlist", "kpi-yellow")

    with c4:
        kpi_card("Pre-Earnings", pre_earnings, "vor Zahlen")

    with c5:
        kpi_card("Post-Earnings", post_earnings, "nach Zahlen")

    with c6:
        kpi_card("Ø 2M-Momentum", format_percent(avg_momentum), "alle Kandidaten")

    c7, c8, c9, c10 = st.columns(4)

    with c7:
        kpi_card("Kandidaten gesamt", stats.get("candidates_total", 0))

    with c8:
        kpi_card("Mit Performance-Daten", stats.get("stocks_with_price_data", 0))

    with c9:
        kpi_card("TradingView Earnings", stats.get("tradingview_earnings_found", 0))

    with c10:
        kpi_card("Datenquellen extern", f"FMP {stats.get('fmp_earnings_found', 0)} · Finnhub {stats.get('finnhub_earnings_found', 0)}")

    if all_df is not None and not all_df.empty:
        best = sort_dataframe(all_df, "score").iloc[0]

        st.markdown(
            f"""
            <div class="top-candidate">
                <div class="top-candidate-label">Bester Kandidat nach Score</div>
                <div class="top-candidate-title">{escape(str(best.get("company", "n/a")))} ({escape(str(best.get("symbol", "n/a")))})</div>
                <div class="top-candidate-meta">
                    Status: <b>{escape(str(best.get("status", "n/a")))}</b> ·
                    Setup: <b>{escape(str(best.get("setup_type", "n/a")))}</b> ·
                    Earnings: <b>{escape(format_date_de(best.get("earnings_date")))}</b> ·
                    Score: <b>{int(best.get("score", 0))} %</b> ·
                    Stage 2: <b>{int(best.get("stage2_score", 0))} %</b> ·
                    2M-Momentum: <b>{escape(format_percent(best.get("performance_2m_proxy_pct")))}</b>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def show_top_control_panel(display_all):
    st.markdown(
        """
        <div class="control-panel">
            <div class="control-title">Analyst Cockpit</div>
            <div class="control-text">
                Hauptsteuerung für Sortierung, Ansicht, News und schnelle Qualitätsfilter. Detailfilter sind optional.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns([1.2, 1.2, 1])

    with c1:
        sort_choice = st.selectbox(
            "Sortierung",
            options=[
                "Score ↓",
                "2M-Momentum ↓",
                "Stage 2 ↓",
                "Earnings früh → spät",
                "Earnings spät → früh",
                "Market Cap ↓",
                "Dollar-Volumen ↓",
                "Abstand 50-Tage ↓",
                "Abstand 200-Tage ↓",
                "Ticker A–Z",
            ],
            index=0,
        )

    with c2:
        view_mode = st.selectbox(
            "Ansicht",
            options=[
                "Treffer + kompakte Tabelle",
                "Nur Treffer",
                "Alle Kandidaten",
                "Tabellenmodus",
                "Charts & Ranking",
                "Vollansicht",
            ],
            index=0,
        )

    with c3:
        quick_filter = st.selectbox(
            "Schnellfilter",
            options=[
                "Alle anzeigen",
                "Nur Momentum-Treffer",
                "Nur A-Setups",
                "Nur A- und B-Setups",
                "Nur Pre-Earnings",
                "Nur Post-Earnings",
            ],
            index=0,
        )

    c4, c5, c6, c7 = st.columns([1, 1, 1, 1])

    with c4:
        min_score_filter = st.slider(
            "Mindest-Score",
            min_value=0,
            max_value=100,
            value=0,
            step=5,
        )

    with c5:
        min_stage2_filter = st.slider(
            "Mindest-Stage-2",
            min_value=0,
            max_value=100,
            value=0,
            step=5,
        )

    with c6:
        min_momentum_filter = st.slider(
            "Mindest-2M-Momentum",
            min_value=-50,
            max_value=200,
            value=-50,
            step=5,
        )

    with c7:
        chart_toggle = st.checkbox(
            "Charts anzeigen",
            value=show_chart_previews,
        )

        news_toggle = st.checkbox(
            "News anzeigen",
            value=show_news,
        )

    sort_map = {
        "Score ↓": "score",
        "2M-Momentum ↓": "momentum",
        "Stage 2 ↓": "stage2",
        "Earnings früh → spät": "earnings_date_asc",
        "Earnings spät → früh": "earnings_date_desc",
        "Market Cap ↓": "market_cap",
        "Dollar-Volumen ↓": "dollar_volume",
        "Abstand 50-Tage ↓": "distance_50",
        "Abstand 200-Tage ↓": "distance_200",
        "Ticker A–Z": "ticker",
    }

    st.session_state.sort_key = sort_map.get(sort_choice, "score")

    status_options = sorted(display_all["status"].dropna().unique())
    setup_options = sorted(display_all["setup_type"].dropna().unique())
    source_options = sorted(display_all["calendar_source"].dropna().unique())
    stage_options = sorted(display_all["stage2_status"].dropna().unique())

    status_filter = status_options
    setup_type_filter = setup_options
    source_filter = source_options
    stage_filter = stage_options

    show_advanced_filters = st.checkbox(
        "Erweiterte Filter anzeigen",
        value=False,
    )

    if show_advanced_filters:
        f1, f2, f3, f4 = st.columns(4)

        with f1:
            status_choice = st.selectbox(
                "Status",
                options=["Alle"] + status_options,
                index=0,
            )

        with f2:
            setup_choice = st.selectbox(
                "Setup",
                options=["Alle"] + setup_options,
                index=0,
            )

        with f3:
            source_choice = st.selectbox(
                "Earnings-Quelle",
                options=["Alle"] + source_options,
                index=0,
            )

        with f4:
            stage_choice = st.selectbox(
                "Stage-2-Status",
                options=["Alle"] + stage_options,
                index=0,
            )

        if status_choice != "Alle":
            status_filter = [status_choice]

        if setup_choice != "Alle":
            setup_type_filter = [setup_choice]

        if source_choice != "Alle":
            source_filter = [source_choice]

        if stage_choice != "Alle":
            stage_filter = [stage_choice]

    st.markdown(
        f"""
        <div class="filter-chip-line">
            <span class="filter-chip">Sortierung: {escape(sort_choice)}</span>
            <span class="filter-chip">Ansicht: {escape(view_mode)}</span>
            <span class="filter-chip">Schnellfilter: {escape(quick_filter)}</span>
            <span class="filter-chip">Score ≥ {min_score_filter}</span>
            <span class="filter-chip">Stage 2 ≥ {min_stage2_filter}</span>
            <span class="filter-chip">2M ≥ {min_momentum_filter} %</span>
            <span class="filter-chip">News: {"an" if news_toggle else "aus"}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    return {
        "view_mode": view_mode,
        "quick_filter": quick_filter,
        "status_filter": status_filter,
        "setup_type_filter": setup_type_filter,
        "source_filter": source_filter,
        "stage_filter": stage_filter,
        "min_score_filter": min_score_filter,
        "min_stage2_filter": min_stage2_filter,
        "min_momentum_filter": min_momentum_filter,
        "chart_toggle": chart_toggle,
        "news_toggle": news_toggle,
    }


def apply_top_filters(df, filters):
    if df is None or df.empty:
        return df

    filtered = df[
        df["status"].isin(filters["status_filter"])
        & df["setup_type"].isin(filters["setup_type_filter"])
        & df["calendar_source"].isin(filters["source_filter"])
        & df["stage2_status"].isin(filters["stage_filter"])
        & (df["score"] >= filters["min_score_filter"])
        & (df["stage2_score"] >= filters["min_stage2_filter"])
        & (df["performance_2m_proxy_pct"] >= filters["min_momentum_filter"])
    ].copy()

    quick_filter = filters["quick_filter"]

    if quick_filter == "Nur Momentum-Treffer":
        filtered = filtered[filtered["performance_2m_proxy_pct"] >= min_performance]

    elif quick_filter == "Nur A-Setups":
        filtered = filtered[filtered["status"] == "A-Setup"]

    elif quick_filter == "Nur A- und B-Setups":
        filtered = filtered[filtered["status"].isin(["A-Setup", "B-Setup"])]

    elif quick_filter == "Nur Pre-Earnings":
        filtered = filtered[filtered["setup_type"] == "Pre-Earnings"]

    elif quick_filter == "Nur Post-Earnings":
        filtered = filtered[filtered["setup_type"] == "Post-Earnings"]

    return sort_dataframe(filtered, st.session_state.sort_key)


def show_candidate_cards(df, title, empty_message, limit=20, show_charts=True, show_news_items=True):
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
        status = row.get("status", "")
        rating = row.get("rating", "Watch")
        stage2_status = row.get("stage2_status", "n/a")
        setup_type = row.get("setup_type", "n/a")
        quality_reason = row.get("quality_reason", "n/a")

        if status in ["A-Setup", "Post-Earnings Winner"]:
            card_class = "stock-header-hit"
        elif status in ["B-Setup", "Treffer", "Watchlist"]:
            card_class = "stock-header-watch"
        elif status == "Ignore":
            card_class = "stock-header-ignore"
        else:
            card_class = ""

        st.markdown(
            f"""
            <div class="stock-header {card_class}">
                <div class="stock-title">{escape(str(company))} ({escape(str(ticker))})</div>
                <div class="stock-meta">
                    WKN: {escape(str(wkn))} · Börse: {escape(str(exchange))} · Setup: {escape(str(setup_type))} ·
                    Earnings-Datum: {escape(str(row["Datum"]))} · Earnings-Quelle: {escape(str(source))}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        left, right = st.columns([2.15, 1])

        with left:
            c1, c2, c3, c4 = st.columns(4)

            with c1:
                st.markdown(metric_box("Earnings-Datum", row["Datum"]), unsafe_allow_html=True)

            with c2:
                st.markdown(metric_box("Aktueller Kurs", row["Kurs"]), unsafe_allow_html=True)

            with c3:
                st.markdown(
                    metric_box(
                        "2M Proxy",
                        row["2M Proxy"],
                        numeric_class(row.get("performance_2m_proxy_pct")),
                    ),
                    unsafe_allow_html=True,
                )

            with c4:
                st.markdown(metric_box("Gesamtscore", f"{int(row['score'])} %"), unsafe_allow_html=True)

            c5, c6, c7, c8 = st.columns(4)

            with c5:
                st.markdown(
                    metric_box_small(
                        "Abstand 50-Tage-Linie",
                        row["Abstand 50-Tage-Linie"],
                        numeric_class(row.get("distance_sma_50_pct")),
                    ),
                    unsafe_allow_html=True,
                )

            with c6:
                st.markdown(
                    metric_box_small(
                        "Abstand 200-Tage-Linie",
                        row["Abstand 200-Tage-Linie"],
                        numeric_class(row.get("distance_sma_200_pct")),
                    ),
                    unsafe_allow_html=True,
                )

            with c7:
                st.markdown(metric_box_small("Stage 2", f"{int(row['stage2_score'])} %"), unsafe_allow_html=True)

            with c8:
                st.markdown(metric_box_small("Earnings-Quelle", source), unsafe_allow_html=True)

            c9, c10, c11 = st.columns(3)

            with c9:
                st.markdown(metric_box_small("Market Cap", row["Marktkapitalisierung"]), unsafe_allow_html=True)

            with c10:
                st.markdown(metric_box_small("Volumen", row["Volumen"]), unsafe_allow_html=True)

            with c11:
                st.markdown(metric_box_small("Dollar-Volumen", row["Dollar-Volumen"]), unsafe_allow_html=True)

            st.markdown(
                f"""
                <div class="badge-row">
                    <span class="badge {status_badge_class(status)}">{escape(str(status))}</span>
                    <span class="badge">{escape(str(rating_badge(rating)))}</span>
                    <span class="badge">{escape(str(stage2_status))}</span>
                    <span class="badge">{escape(str(setup_type))}</span>
                    <span class="badge">Rel. SPY: {escape(str(row["Relativ zu SPY"]))}</span>
                    <span class="badge">Rel. QQQ: {escape(str(row["Relativ zu QQQ"]))}</span>
                    <span class="badge">1M: {escape(str(row["1M"]))}</span>
                    <span class="badge">3M: {escape(str(row["3M"]))}</span>
                    <span class="badge">6M: {escape(str(row["6M"]))}</span>
                </div>
                <div class="info-line">
                    <b>Aktion:</b> {escape(str(action))} · <b>Kursdaten:</b> {escape(str(data_source))}<br>
                    <b>Qualität:</b> {escape(str(quality_reason))}
                </div>
                """,
                unsafe_allow_html=True,
            )

            if interpretation:
                st.info(interpretation)

            if chart_url:
                st.link_button("TradingView öffnen", chart_url, use_container_width=True)

            if show_news_items:
                show_news_block(ticker, company, max_news_per_stock)

        with right:
            if show_charts:
                show_chart_preview(ticker)

        st.divider()


def show_compact_table(df, title):
    st.subheader(title)

    if df is None or df.empty:
        st.warning("Keine Daten vorhanden.")
        return

    display = prepare_display_df(df)

    compact = display[
        [
            "company",
            "symbol",
            "wkn",
            "exchange",
            "setup_type",
            "Datum",
            "calendar_source",
            "Kurs",
            "Marktkapitalisierung",
            "Dollar-Volumen",
            "2M Proxy",
            "Abstand 50-Tage-Linie",
            "Abstand 200-Tage-Linie",
            "stage2_score",
            "score",
            "status",
            "quality_reason",
            "chart_url",
        ]
    ].rename(
        columns={
            "company": "Unternehmen",
            "symbol": "Ticker",
            "wkn": "WKN",
            "exchange": "Börse",
            "setup_type": "Setup",
            "calendar_source": "Earnings-Quelle",
            "stage2_score": "Stage 2",
            "score": "Score",
            "status": "Status",
            "quality_reason": "Qualität",
            "chart_url": "Chart",
        }
    )

    st.dataframe(
        compact,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Stage 2": st.column_config.ProgressColumn(
                "Stage 2",
                min_value=0,
                max_value=100,
            ),
            "Score": st.column_config.ProgressColumn(
                "Score",
                min_value=0,
                max_value=100,
            ),
            "Chart": st.column_config.LinkColumn(
                "Chart",
                display_text="öffnen",
            ),
        },
    )


def show_detail_table(df):
    if df is None or df.empty:
        return

    display = prepare_display_df(df)

    detail = display.rename(
        columns={
            "symbol": "Ticker",
            "company": "Unternehmen",
            "wkn": "WKN",
            "isin": "ISIN",
            "exchange": "Börse",
            "sector": "Sektor",
            "industry": "Industrie",
            "setup_type": "Setup",
            "earnings_date": "Earnings-Datum roh",
            "calendar_source": "Earnings-Quelle",
            "current_close": "Aktueller Kurs roh",
            "market_cap_m": "Market Cap Mio.",
            "volume": "Volumen",
            "dollar_volume_m": "Dollar-Volumen Mio.",
            "performance_1m_pct": "1M-Performance %",
            "performance_3m_pct": "3M-Performance %",
            "performance_6m_pct": "6M-Performance %",
            "performance_2m_proxy_pct": "2M-Performance Proxy %",
            "spy_relative_proxy_pct": "Relativ zu SPY %",
            "qqq_relative_proxy_pct": "Relativ zu QQQ %",
            "above_sma_50": "Über 50-Tage-Linie",
            "above_sma_200": "Über 200-Tage-Linie",
            "distance_sma_50_pct": "Abstand 50-Tage-Linie %",
            "distance_sma_200_pct": "Abstand 200-Tage-Linie %",
            "stage2_score": "Stage-2-Score",
            "stage2_status": "Stage-2-Status",
            "score": "Gesamtscore",
            "rating": "Rating",
            "status": "Status",
            "quality_pass": "Qualitätsfilter erfüllt",
            "quality_reason": "Qualität",
            "interpretation": "Interpretation",
            "action": "Aktion",
            "chart_url": "Chart öffnen",
            "data_source": "Datenquelle",
        }
    )

    st.dataframe(
        detail,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Chart öffnen": st.column_config.LinkColumn(
                "Chart öffnen",
                display_text="TradingView öffnen",
            ),
            "Stage-2-Score": st.column_config.ProgressColumn(
                "Stage-2-Score",
                min_value=0,
                max_value=100,
            ),
            "Gesamtscore": st.column_config.ProgressColumn(
                "Gesamtscore",
                min_value=0,
                max_value=100,
            ),
        },
    )


def show_explanation_box(min_performance):
    st.markdown(
        f"""
        <div class="panel">
            <div class="panel-title">Lesart</div>
            <div class="panel-text">
                <b>A-Setup:</b> starkes Momentum, hohe Trendqualität, Qualitätsfilter erfüllt.<br>
                <b>B-Setup:</b> Momentum vorhanden, aber nicht perfekt.<br>
                <b>Pre-Earnings:</b> Zahlen stehen noch bevor. Das ist dein Hauptscreening für Vorlauf-Momentum.<br>
                <b>Post-Earnings:</b> Zahlen wurden bereits gemeldet. Das ist eine Reaktions-/Follow-Through-Liste.<br>
                <b>Treffer:</b> geschätzte 2M-Performance liegt bei mindestens {min_performance:.0f} %.<br>
                <b>Qualitätsfilter:</b> entfernt OTC, Pennystocks, Microcaps und illiquide Aktien.<br>
                <b>News:</b> API-News werden gecacht. Deutsche News werden über Google News geöffnet.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


if manual_check:
    st.subheader(f"Manuelle Prüfung: {manual_symbol.upper()}")

    with st.spinner("Ticker wird geprüft..."):
        manual_df = analyze_single_symbol(
            symbol=manual_symbol,
            min_performance_2m=min_performance,
        )

    if manual_df is None or manual_df.empty:
        st.error("Ticker konnte nicht geprüft werden.")
    else:
        show_candidate_cards(
            manual_df,
            title="Ticker-Ergebnis",
            empty_message="Keine Daten gefunden.",
            limit=1,
            show_charts=show_chart_previews,
            show_news_items=show_news,
        )

        with st.expander("Technische Detaildaten anzeigen"):
            show_detail_table(manual_df)

    st.stop()


if run_now:
    with st.spinner("Screener läuft. TradingView-Daten werden geladen und gefiltert..."):
        hits_df, all_df, stats = run_screen(
            lookback_days=lookback_days,
            forward_days=forward_days,
            min_performance_2m=min_performance,
            tradingview_limit=tradingview_limit,
            min_price=min_price,
            min_market_cap_m=min_market_cap_m,
            min_volume=min_volume,
            min_dollar_volume_m=min_dollar_volume_m,
            allowed_exchanges=allowed_exchanges,
            exclude_otc=exclude_otc,
            apply_quality_filter=apply_quality_filter,
            setup_filter=setup_filter,
        )

    st.session_state.hits_df = hits_df
    st.session_state.all_df = all_df
    st.session_state.stats = stats
    st.session_state.has_results = True


if not st.session_state.has_results:
    st.info("Klicke links auf **Screener jetzt ausführen**.")
    show_explanation_box(min_performance)
    st.stop()


hits_df = st.session_state.hits_df
all_df = st.session_state.all_df
stats = st.session_state.stats


if stats.get("tradingview_error"):
    st.warning(f"TradingView-Quelle: {stats['tradingview_error']}")

if all_df is None or all_df.empty:
    show_screening_summary(stats, all_df, hits_df)
    st.warning("Keine Kandidaten mit verwertbaren TradingView-Performance-Daten.")
    show_explanation_box(min_performance)
    st.stop()


show_screening_summary(stats, all_df, hits_df)

display_all = prepare_display_df(all_df)

filters = show_top_control_panel(display_all)

filtered_all = apply_top_filters(all_df, filters)
filtered_hits = apply_top_filters(hits_df, filters)

st.divider()

view_mode = filters["view_mode"]

if view_mode == "Treffer + kompakte Tabelle":
    show_candidate_cards(
        filtered_hits,
        title="Treffer: Aktien über Momentum-Filter",
        empty_message="Keine Aktie erfüllt aktuell deine Filter.",
        limit=max_cards,
        show_charts=filters["chart_toggle"],
        show_news_items=filters["news_toggle"],
    )

    st.divider()

    show_compact_table(
        filtered_all,
        title="Kompakte Tabelle",
    )

elif view_mode == "Nur Treffer":
    show_candidate_cards(
        filtered_hits,
        title="Treffer: Aktien über Momentum-Filter",
        empty_message="Keine Aktie erfüllt aktuell deine Filter.",
        limit=max_cards,
        show_charts=filters["chart_toggle"],
        show_news_items=filters["news_toggle"],
    )

elif view_mode == "Alle Kandidaten":
    show_candidate_cards(
        filtered_all,
        title="Alle geprüften Kandidaten — Kartenansicht",
        empty_message="Keine Kandidaten nach Filter.",
        limit=max_cards,
        show_charts=filters["chart_toggle"],
        show_news_items=filters["news_toggle"],
    )

elif view_mode == "Tabellenmodus":
    show_compact_table(
        filtered_all,
        title="Kompakte Tabelle",
    )

    with st.expander("Technische Detailtabelle öffnen"):
        show_detail_table(filtered_all)

elif view_mode == "Charts & Ranking":
    st.subheader("Top 15 nach Gesamtscore")

    top15_score = filtered_all.sort_values("score", ascending=False).head(15)

    st.bar_chart(
        top15_score.rename(columns={"symbol": "Ticker", "score": "Gesamtscore"}),
        x="Ticker",
        y="Gesamtscore",
    )

    st.divider()

    st.subheader("Top 15 nach 2M-Performance Proxy")

    top15_momentum = filtered_all.sort_values(
        "performance_2m_proxy_pct",
        ascending=False,
    ).head(15)

    st.bar_chart(
        top15_momentum.rename(
            columns={
                "symbol": "Ticker",
                "performance_2m_proxy_pct": "2M-Performance Proxy %",
            }
        ),
        x="Ticker",
        y="2M-Performance Proxy %",
    )

elif view_mode == "Vollansicht":
    show_candidate_cards(
        filtered_hits,
        title="Treffer: Aktien über Momentum-Filter",
        empty_message="Keine Aktie erfüllt aktuell deine Filter.",
        limit=max_cards,
        show_charts=filters["chart_toggle"],
        show_news_items=filters["news_toggle"],
    )

    st.divider()

    show_candidate_cards(
        filtered_all,
        title="Alle geprüften Kandidaten — Kartenansicht",
        empty_message="Keine Kandidaten nach Filter.",
        limit=max_cards,
        show_charts=filters["chart_toggle"],
        show_news_items=filters["news_toggle"],
    )

    st.divider()

    show_compact_table(
        filtered_all,
        title="Kompakte Tabelle",
    )

    with st.expander("Technische Detailtabelle öffnen"):
        show_detail_table(filtered_all)

    st.divider()

    st.subheader("Top 15 nach Gesamtscore")

    top15_score = filtered_all.sort_values("score", ascending=False).head(15)

    st.bar_chart(
        top15_score.rename(columns={"symbol": "Ticker", "score": "Gesamtscore"}),
        x="Ticker",
        y="Gesamtscore",
    )

    st.subheader("Top 15 nach 2M-Performance Proxy")

    top15_momentum = filtered_all.sort_values(
        "performance_2m_proxy_pct",
        ascending=False,
    ).head(15)

    st.bar_chart(
        top15_momentum.rename(
            columns={
                "symbol": "Ticker",
                "performance_2m_proxy_pct": "2M-Performance Proxy %",
            }
        ),
        x="Ticker",
        y="2M-Performance Proxy %",
    )

st.divider()

with st.expander("Lesart und Methodik öffnen"):
    show_explanation_box(min_performance)

st.caption(
    "Keine Anlageberatung. TradingView-, Finnhub- und FMP-Daten dienen als Screening-Grundlage. "
    "Treffer müssen manuell im Chart, fundamental und über Primärquellen geprüft werden."
)
