import pandas as pd
import streamlit as st

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

        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] div {
            color: #F8FAFC !important;
            opacity: 1 !important;
        }

        [data-testid="stSidebar"] input {
            background: #0F1726 !important;
            color: #FFFFFF !important;
            border: 1px solid rgba(255,255,255,0.28) !important;
        }

        [data-baseweb="select"] {
            background: #0F1726 !important;
            color: #FFFFFF !important;
            border-radius: 10px !important;
        }

        [data-baseweb="select"] * {
            color: #FFFFFF !important;
            opacity: 1 !important;
        }

        [data-baseweb="tag"] {
            background: #EF4444 !important;
            color: #FFFFFF !important;
            border-radius: 7px !important;
        }

        [data-baseweb="tag"] * {
            color: #FFFFFF !important;
            opacity: 1 !important;
            font-weight: 800 !important;
        }

        [role="listbox"],
        [role="option"] {
            background: #111827 !important;
            color: #FFFFFF !important;
        }

        [role="option"] * {
            color: #FFFFFF !important;
        }

        .block-container {
            padding-top: 1.7rem;
            padding-left: 2.1rem;
            padding-right: 2.1rem;
            max-width: 1600px;
        }

        h1, h2, h3, h4 {
            color: #FFFFFF !important;
            letter-spacing: -0.02em;
        }

        p, span, div, label {
            color: inherit;
        }

        .main-header {
            padding: 20px 24px;
            border-radius: 22px;
            background: linear-gradient(135deg, #1E293B 0%, #172033 100%);
            border: 1px solid rgba(255,255,255,0.18);
            box-shadow: 0 12px 30px rgba(0,0,0,0.32);
            margin-bottom: 24px;
        }

        .main-title {
            font-size: 36px;
            font-weight: 850;
            line-height: 1.08;
            margin-bottom: 7px;
            color: #FFFFFF;
        }

        .main-subtitle {
            font-size: 14px;
            color: #E2E8F0;
        }

        .summary-card {
            background: #1B263A;
            border: 1px solid rgba(255,255,255,0.22);
            border-radius: 20px;
            padding: 18px 20px;
            margin-bottom: 18px;
            box-shadow: 0 10px 24px rgba(0,0,0,0.24);
        }

        .summary-title {
            font-size: 22px;
            font-weight: 850;
            margin-bottom: 8px;
            color: #FFFFFF;
        }

        .summary-text {
            font-size: 14px;
            color: #F8FAFC;
            line-height: 1.45;
            font-weight: 650;
        }

        .summary-grid {
            display: grid;
            grid-template-columns: repeat(6, minmax(0, 1fr));
            gap: 12px;
            margin-top: 16px;
            margin-bottom: 14px;
        }

        .summary-grid-3 {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 12px;
            margin-bottom: 14px;
        }

        .summary-metric {
            background: #1B263A;
            border: 1px solid rgba(255,255,255,0.24);
            border-radius: 16px;
            padding: 13px 14px;
            min-height: 76px;
            box-shadow: 0 6px 16px rgba(0,0,0,0.20);
        }

        .summary-metric-label {
            color: #FFFFFF;
            font-size: 12px;
            font-weight: 850;
            opacity: 1;
            margin-bottom: 8px;
        }

        .summary-metric-value {
            color: #FFFFFF;
            font-size: 28px;
            font-weight: 900;
            line-height: 1.05;
            opacity: 1;
        }

        .summary-metric-delta {
            display: inline-flex;
            margin-top: 6px;
            border-radius: 999px;
            padding: 4px 8px;
            font-size: 12px;
            font-weight: 850;
            background: rgba(34,197,94,0.20);
            color: #BBF7D0;
        }

        .stock-card {
            background: #162032;
            border: 1px solid rgba(255,255,255,0.18);
            border-radius: 22px;
            padding: 18px;
            margin-bottom: 18px;
            box-shadow: 0 12px 28px rgba(0,0,0,0.30);
        }

        .stock-card-hit {
            border-color: rgba(34,197,94,0.78);
            box-shadow: 0 0 0 1px rgba(34,197,94,0.24), 0 12px 28px rgba(0,0,0,0.30);
        }

        .stock-card-watch {
            border-color: rgba(245,158,11,0.60);
        }

        .stock-card-ignore {
            border-color: rgba(239,68,68,0.55);
            opacity: 0.88;
        }

        .stock-title {
            font-size: 22px;
            font-weight: 850;
            color: #FFFFFF;
            margin-bottom: 4px;
        }

        .stock-meta {
            color: #F1F5F9;
            font-size: 12px;
            margin-bottom: 12px;
            font-weight: 700;
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
            white-space: nowrap;
            font-weight: 850;
            opacity: 1;
        }

        .metric-value {
            font-size: 20px;
            line-height: 1.15;
            font-weight: 900;
            color: #FFFFFF;
            white-space: nowrap;
            opacity: 1;
        }

        .metric-value-small {
            font-size: 17px;
            line-height: 1.15;
            font-weight: 900;
            color: #FFFFFF;
            white-space: nowrap;
            opacity: 1;
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

        .sort-panel {
            background: #1B263A;
            border: 1px solid rgba(255,255,255,0.22);
            border-radius: 20px;
            padding: 16px 18px;
            margin-top: 18px;
            margin-bottom: 20px;
            box-shadow: 0 10px 24px rgba(0,0,0,0.24);
        }

        .sort-title {
            font-size: 20px;
            font-weight: 850;
            color: #FFFFFF;
            margin-bottom: 6px;
        }

        .sort-hint {
            color: #F8FAFC;
            font-size: 13px;
            margin-bottom: 12px;
            font-weight: 650;
        }

        .sort-active {
            display: inline-flex;
            border-radius: 999px;
            padding: 6px 12px;
            font-size: 12px;
            font-weight: 850;
            background: rgba(37,99,235,0.28);
            border: 1px solid rgba(37,99,235,0.68);
            color: #DBEAFE;
            margin-top: 10px;
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

        @media (max-width: 1200px) {
            .summary-grid {
                grid-template-columns: repeat(3, minmax(0, 1fr));
            }

            .summary-grid-3 {
                grid-template-columns: repeat(1, minmax(0, 1fr));
            }
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
            Analysten-Dashboard · Qualitätsfilter · Pre-/Post-Earnings · Momentum · 50-/200-Tage-Linie · Chartvorschau
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


st.sidebar.header("Steuerung")

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

show_chart_previews = st.sidebar.checkbox(
    "Chart-Vorschau anzeigen",
    value=True,
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
            <img src="{url}" alt="Chart {ticker}" />
            <div class="chart-caption">
                Chart-Vorschau {ticker} · Für Detailanalyse den TradingView-Link öffnen
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_box(label, value, css_class=""):
    return f"""
    <div class="metric-box">
        <div class="metric-label">{label}</div>
        <div class="metric-value {css_class}">{value}</div>
    </div>
    """


def metric_box_small(label, value, css_class=""):
    return f"""
    <div class="metric-box">
        <div class="metric-label">{label}</div>
        <div class="metric-value-small {css_class}">{value}</div>
    </div>
    """


def summary_metric(label, value, delta=None):
    delta_html = ""

    if delta is not None:
        delta_html = f'<div class="summary-metric-delta">{delta}</div>'

    return f"""
    <div class="summary-metric">
        <div class="summary-metric-label">{label}</div>
        <div class="summary-metric-value">{value}</div>
        {delta_html}
    </div>
    """


def show_screening_summary(stats):
    start_date = format_date_de(stats.get("start_date"))
    end_date = format_date_de(stats.get("end_date"))
    hits = stats.get("hits", 0)
    min_perf = stats.get("min_performance_2m", 0)

    if hits > 0:
        result_text = f"{hits} Aktie(n) erfüllen den Momentum-Filter von mindestens {min_perf:.0f} %."
        result_color = "positive"
    else:
        result_text = f"Kein Treffer über {min_perf:.0f} %. Der Filter ist aktuell streng oder der Zeitraum unattraktiv."
        result_color = "neutral"

    st.markdown(
        f"""
        <div class="summary-card">
            <div class="summary-title">Screening-Übersicht</div>
            <div class="summary-text">
                Zeitraum: <b>{start_date}</b> bis <b>{end_date}</b><br>
                Ergebnis: <span class="{result_color}"><b>{result_text}</b></span><br>
                Qualitätsfilter: Kurs ≥ {stats.get("min_price")} USD · Market Cap ≥ {stats.get("min_market_cap_m")} Mio. USD ·
                Volumen ≥ {format_number(stats.get("min_volume"))} · Dollar-Volumen ≥ {stats.get("min_dollar_volume_m")} Mio. USD
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="summary-grid">
            {summary_metric("FMP Earnings", stats.get("fmp_earnings_found", 0))}
            {summary_metric("Finnhub Earnings", stats.get("finnhub_earnings_found", 0))}
            {summary_metric("TradingView Earnings", stats.get("tradingview_earnings_found", 0))}
            {summary_metric("Kandidaten gesamt", stats.get("candidates_total", 0))}
            {summary_metric("Mit Performance-Daten", stats.get("stocks_with_price_data", 0))}
            {summary_metric("Treffer", hits)}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="summary-grid-3">
            {summary_metric("SPY 2M", format_percent(stats.get("spy_perf_2m")))}
            {summary_metric("QQQ 2M", format_percent(stats.get("qqq_perf_2m")))}
            {summary_metric("Setup-Filter", stats.get("setup_filter", "Alle"))}
        </div>
        """,
        unsafe_allow_html=True,
    )

    if stats.get("best_symbol") is not None:
        st.markdown(
            f"""
            <div class="summary-card">
                <div class="summary-text">Bester geprüfter Kandidat</div>
                <div class="summary-title">{stats.get("best_company")} ({stats.get("best_symbol")})</div>
                <span class="summary-metric-delta">{format_percent(stats.get("best_performance"))}</span>
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


def show_sort_buttons():
    st.markdown(
        """
        <div class="sort-panel">
            <div class="sort-title">Sortierung</div>
            <div class="sort-hint">
                Diese Sortierung wirkt auf Treffer und alle Kandidaten. Die Ergebnisse bleiben beim Sortieren gespeichert.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    b1, b2, b3, b4 = st.columns(4)

    with b1:
        if st.button("Score ↓", use_container_width=True, key="sort_score_top"):
            st.session_state.sort_key = "score"

    with b2:
        if st.button("2M-Momentum ↓", use_container_width=True, key="sort_momentum_top"):
            st.session_state.sort_key = "momentum"

    with b3:
        if st.button("Stage 2 ↓", use_container_width=True, key="sort_stage2_top"):
            st.session_state.sort_key = "stage2"

    with b4:
        if st.button("Ticker A–Z", use_container_width=True, key="sort_ticker_top"):
            st.session_state.sort_key = "ticker"

    b5, b6, b7, b8 = st.columns(4)

    with b5:
        if st.button("Earnings früh → spät", use_container_width=True, key="sort_earnings_asc_top"):
            st.session_state.sort_key = "earnings_date_asc"

    with b6:
        if st.button("Earnings spät → früh", use_container_width=True, key="sort_earnings_desc_top"):
            st.session_state.sort_key = "earnings_date_desc"

    with b7:
        if st.button("Market Cap ↓", use_container_width=True, key="sort_market_cap_top"):
            st.session_state.sort_key = "market_cap"

    with b8:
        if st.button("Dollar-Volumen ↓", use_container_width=True, key="sort_dollar_volume_top"):
            st.session_state.sort_key = "dollar_volume"

    b9, b10 = st.columns(2)

    with b9:
        if st.button("Abstand 50-Tage ↓", use_container_width=True, key="sort_distance50_top"):
            st.session_state.sort_key = "distance_50"

    with b10:
        if st.button("Abstand 200-Tage ↓", use_container_width=True, key="sort_distance200_top"):
            st.session_state.sort_key = "distance_200"

    sort_labels = {
        "score": "Score absteigend",
        "momentum": "2M-Momentum absteigend",
        "stage2": "Stage 2 absteigend",
        "ticker": "Ticker A–Z",
        "earnings_date_asc": "Earnings früh → spät",
        "earnings_date_desc": "Earnings spät → früh",
        "distance_50": "Abstand zur 50-Tage-Linie absteigend",
        "distance_200": "Abstand zur 200-Tage-Linie absteigend",
        "market_cap": "Marktkapitalisierung absteigend",
        "dollar_volume": "Dollar-Volumen absteigend",
    }

    st.markdown(
        f"""
        <div class="sort-active">
            Aktive Sortierung: {sort_labels.get(st.session_state.sort_key, 'Score absteigend')}
        </div>
        """,
        unsafe_allow_html=True,
    )


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
        status = row.get("status", "")
        rating = row.get("rating", "Watch")
        stage2_status = row.get("stage2_status", "n/a")
        setup_type = row.get("setup_type", "n/a")
        quality_reason = row.get("quality_reason", "n/a")

        if status in ["A-Setup", "Post-Earnings Winner"]:
            card_class = "stock-card-hit"
        elif status in ["B-Setup", "Treffer", "Watchlist"]:
            card_class = "stock-card-watch"
        elif status == "Ignore":
            card_class = "stock-card-ignore"
        else:
            card_class = ""

        with st.container():
            st.markdown(
                f"""
                <div class="stock-card {card_class}">
                    <div class="stock-title">{company} ({ticker})</div>
                    <div class="stock-meta">
                        WKN: {wkn} · Börse: {exchange} · Setup: {setup_type} ·
                        Earnings-Datum: {row['Datum']} · Earnings-Quelle: {source}
                    </div>
                """,
                unsafe_allow_html=True,
            )

            left, right = st.columns([2.15, 1])

            with left:
                c1, c2, c3, c4 = st.columns(4)

                with c1:
                    st.markdown(
                        metric_box("Earnings-Datum", row["Datum"]),
                        unsafe_allow_html=True,
                    )

                with c2:
                    st.markdown(
                        metric_box("Aktueller Kurs", row["Kurs"]),
                        unsafe_allow_html=True,
                    )

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
                    st.markdown(
                        metric_box("Gesamtscore", f"{int(row['score'])} %"),
                        unsafe_allow_html=True,
                    )

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
                    st.markdown(
                        metric_box_small("Stage 2", f"{int(row['stage2_score'])} %"),
                        unsafe_allow_html=True,
                    )

                with c8:
                    st.markdown(
                        metric_box_small("Earnings-Quelle", source),
                        unsafe_allow_html=True,
                    )

                c9, c10, c11 = st.columns(3)

                with c9:
                    st.markdown(
                        metric_box_small("Market Cap", row["Marktkapitalisierung"]),
                        unsafe_allow_html=True,
                    )

                with c10:
                    st.markdown(
                        metric_box_small("Volumen", row["Volumen"]),
                        unsafe_allow_html=True,
                    )

                with c11:
                    st.markdown(
                        metric_box_small("Dollar-Volumen", row["Dollar-Volumen"]),
                        unsafe_allow_html=True,
                    )

                st.markdown(
                    f"""
                    <div class="badge-row">
                        <span class="badge {status_badge_class(status)}">{status}</span>
                        <span class="badge">{rating_badge(rating)}</span>
                        <span class="badge">{stage2_status}</span>
                        <span class="badge">{setup_type}</span>
                        <span class="badge">Rel. SPY: {row['Relativ zu SPY']}</span>
                        <span class="badge">Rel. QQQ: {row['Relativ zu QQQ']}</span>
                        <span class="badge">1M: {row['1M']}</span>
                        <span class="badge">3M: {row['3M']}</span>
                        <span class="badge">6M: {row['6M']}</span>
                    </div>
                    <div class="info-line">
                        <b>Aktion:</b> {action} · <b>Kursdaten:</b> {data_source}<br>
                        <b>Qualität:</b> {quality_reason}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if interpretation:
                    st.info(interpretation)

                if chart_url:
                    st.link_button("TradingView öffnen", chart_url, use_container_width=False)

            with right:
                if show_charts:
                    show_chart_preview(ticker)

            st.markdown("</div>", unsafe_allow_html=True)


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
        <div class="summary-card">
            <div class="summary-title">Lesart</div>
            <div class="summary-text">
                <b>A-Setup:</b> starkes Momentum, hohe Trendqualität, Qualitätsfilter erfüllt.<br>
                <b>B-Setup:</b> Momentum vorhanden, aber nicht perfekt.<br>
                <b>Pre-Earnings:</b> Zahlen stehen noch bevor. Das ist dein Hauptscreening für Vorlauf-Momentum.<br>
                <b>Post-Earnings:</b> Zahlen wurden bereits gemeldet. Das ist eine Reaktions-/Follow-Through-Liste.<br>
                <b>Treffer:</b> geschätzte 2M-Performance liegt bei mindestens {min_performance:.0f} %.<br>
                <b>Qualitätsfilter:</b> entfernt OTC, Pennystocks, Microcaps und illiquide Aktien.<br>
                <b>Stage-2-Score:</b> technische Trendqualität über Kurs, 50-Tage-Linie, 200-Tage-Linie und Performance.
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

show_screening_summary(stats)

st.divider()

if all_df is None or all_df.empty:
    st.warning("Keine Kandidaten mit verwertbaren TradingView-Performance-Daten.")
    show_explanation_box(min_performance)
    st.stop()


display_all = prepare_display_df(all_df)

st.subheader("Sortierung")
show_sort_buttons()

hits_sorted = sort_dataframe(hits_df, st.session_state.sort_key)
all_sorted = sort_dataframe(all_df, st.session_state.sort_key)

st.divider()

show_candidate_cards(
    hits_sorted,
    title="Treffer: Aktien über Momentum-Filter",
    empty_message="Keine Aktie erfüllt aktuell deinen Momentum-Filter.",
    limit=max_cards,
    show_charts=show_chart_previews,
)

st.divider()

st.subheader("Filter für alle Kandidaten")

f1, f2, f3, f4 = st.columns(4)

with f1:
    status_filter = st.multiselect(
        "Status",
        options=sorted(display_all["status"].dropna().unique()),
        default=sorted(display_all["status"].dropna().unique()),
    )

with f2:
    setup_type_filter = st.multiselect(
        "Setup",
        options=sorted(display_all["setup_type"].dropna().unique()),
        default=sorted(display_all["setup_type"].dropna().unique()),
    )

with f3:
    source_filter = st.multiselect(
        "Earnings-Quelle",
        options=sorted(display_all["calendar_source"].dropna().unique()),
        default=sorted(display_all["calendar_source"].dropna().unique()),
    )

with f4:
    stage_filter = st.multiselect(
        "Stage-2-Status",
        options=sorted(display_all["stage2_status"].dropna().unique()),
        default=sorted(display_all["stage2_status"].dropna().unique()),
    )

filtered_all = all_df[
    all_df["status"].isin(status_filter)
    & all_df["setup_type"].isin(setup_type_filter)
    & all_df["calendar_source"].isin(source_filter)
    & all_df["stage2_status"].isin(stage_filter)
]

filtered_all = sort_dataframe(filtered_all, st.session_state.sort_key)

st.divider()

show_candidate_cards(
    filtered_all,
    title="Alle geprüften Kandidaten — Kartenansicht",
    empty_message="Keine Kandidaten nach Filter.",
    limit=max_cards,
    show_charts=show_chart_previews,
)

with st.expander("Kompakte Tabelle anzeigen"):
    show_compact_table(
        filtered_all,
        title="Alle geprüften Kandidaten — kompakte Übersicht",
    )

with st.expander("Technische Detailtabelle anzeigen"):
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

show_explanation_box(min_performance)

st.caption(
    "Keine Anlageberatung. TradingView-Daten dienen als Screening-Grundlage. "
    "Treffer müssen manuell im Chart und fundamental geprüft werden."
)
