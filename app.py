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
            color: #E8EEF7;
        }

        [data-testid="stSidebar"] {
            background: #111827;
            border-right: 1px solid rgba(255,255,255,0.08);
        }

        [data-testid="stSidebar"] * {
            color: #E8EEF7;
        }

        .block-container {
            padding-top: 1.7rem;
            padding-left: 2.1rem;
            padding-right: 2.1rem;
            max-width: 1580px;
        }

        h1, h2, h3, h4 {
            color: #F8FAFC !important;
            letter-spacing: -0.02em;
        }

        .main-header {
            padding: 20px 24px;
            border-radius: 22px;
            background: linear-gradient(135deg, #1E293B 0%, #172033 100%);
            border: 1px solid rgba(255,255,255,0.12);
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
            color: #CBD5E1;
        }

        .summary-card {
            background: #182235;
            border: 1px solid rgba(255,255,255,0.10);
            border-radius: 20px;
            padding: 18px 20px;
            margin-bottom: 18px;
            box-shadow: 0 10px 24px rgba(0,0,0,0.24);
        }

        .summary-title {
            font-size: 22px;
            font-weight: 820;
            margin-bottom: 8px;
            color: #F8FAFC;
        }

        .summary-text {
            font-size: 14px;
            color: #CBD5E1;
            line-height: 1.45;
        }

        .stock-card {
            background: #162032;
            border: 1px solid rgba(255,255,255,0.11);
            border-radius: 22px;
            padding: 18px;
            margin-bottom: 18px;
            box-shadow: 0 12px 28px rgba(0,0,0,0.30);
        }

        .stock-card-hit {
            border-color: rgba(34,197,94,0.65);
            box-shadow: 0 0 0 1px rgba(34,197,94,0.18), 0 12px 28px rgba(0,0,0,0.30);
        }

        .stock-card-watch {
            border-color: rgba(245,158,11,0.48);
        }

        .stock-title {
            font-size: 22px;
            font-weight: 850;
            color: #FFFFFF;
            margin-bottom: 4px;
        }

        .stock-meta {
            color: #B8C4D6;
            font-size: 12px;
            margin-bottom: 12px;
        }

        .metric-box {
            background: #0F1726;
            border: 1px solid rgba(255,255,255,0.09);
            border-radius: 15px;
            padding: 10px 11px;
            min-height: 72px;
        }

        .metric-label {
            font-size: 11px;
            color: #AAB7CA;
            margin-bottom: 5px;
            white-space: nowrap;
        }

        .metric-value {
            font-size: 20px;
            line-height: 1.15;
            font-weight: 820;
            color: #FFFFFF;
            white-space: nowrap;
        }

        .metric-value-small {
            font-size: 17px;
            line-height: 1.15;
            font-weight: 820;
            color: #FFFFFF;
            white-space: nowrap;
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
            color: #CBD5E1 !important;
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
            font-weight: 750;
            border: 1px solid rgba(255,255,255,0.12);
            background: #0F1726;
            color: #DDE6F3;
        }

        .badge-green {
            background: rgba(34,197,94,0.14);
            border-color: rgba(34,197,94,0.44);
            color: #86EFAC;
        }

        .badge-yellow {
            background: rgba(245,158,11,0.14);
            border-color: rgba(245,158,11,0.44);
            color: #FCD34D;
        }

        .badge-red {
            background: rgba(239,68,68,0.14);
            border-color: rgba(239,68,68,0.44);
            color: #FCA5A5;
        }

        .badge-blue {
            background: rgba(59,130,246,0.14);
            border-color: rgba(59,130,246,0.44);
            color: #93C5FD;
        }

        .info-line {
            color: #CAD5E6;
            font-size: 13px;
            line-height: 1.45;
            margin-top: 8px;
        }

        .chart-wrap {
            background: #0B0F17;
            border: 1px solid rgba(255,255,255,0.10);
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
            color: #9BA8BC;
            margin-top: 6px;
        }

        .stButton > button,
        .stLinkButton > a {
            background: #2563EB !important;
            color: white !important;
            border: 1px solid rgba(255,255,255,0.12) !important;
            border-radius: 12px !important;
            font-weight: 800 !important;
            box-shadow: 0 6px 16px rgba(37,99,235,0.22);
        }

        .stButton > button:hover,
        .stLinkButton > a:hover {
            background: #1D4ED8 !important;
            color: white !important;
            border-color: rgba(255,255,255,0.18) !important;
        }

        div[data-testid="stMetric"] {
            background: #182235;
            border: 1px solid rgba(255,255,255,0.10);
            border-radius: 16px;
            padding: 13px 14px;
            box-shadow: 0 6px 16px rgba(0,0,0,0.20);
        }

        div[data-testid="stMetricLabel"] {
            color: #CBD5E1 !important;
        }

        div[data-testid="stMetricValue"] {
            color: #FFFFFF !important;
        }

        .stAlert {
            border-radius: 16px;
        }

        [data-testid="stDataFrame"] {
            background: #182235;
            border-radius: 16px;
            overflow: hidden;
        }

        hr {
            border-color: rgba(255,255,255,0.09);
        }
    </style>
    """,
    unsafe_allow_html=True,
)


st.markdown(
    """
    <div class="main-header">
        <div class="main-title">Earnings Momentum Screener</div>
        <div class="main-subtitle">
            Analysten-Dashboard · Earnings-Kandidaten · Momentum · 50-/200-Tage-Linie · kompakte Chartvorschau
        </div>
    </div>
    """,
    unsafe_allow_html=True,
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
    help="Zeigt pro Aktie eine kompakte Chart-Bildvorschau direkt in der Karte.",
)

max_cards = st.sidebar.slider(
    "Maximale Karten anzeigen",
    min_value=5,
    max_value=50,
    value=20,
    step=5,
    help="Mehr Karten bedeuten mehr Chart-Vorschauen und längere Ladezeit.",
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
    if status == "Treffer":
        return "badge-green"

    if status == "Knapp darunter":
        return "badge-yellow"

    if status == "Schwach":
        return "badge-red"

    if status == "Keine Daten":
        return ""

    return "badge-blue"


def rating_badge(rating):
    if rating == "A":
        return "A-Setup"

    if rating == "B":
        return "B-Setup"

    if rating == "C":
        return "C-Setup"

    return "Watch"


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
                Ergebnis: <span class="{result_color}"><b>{result_text}</b></span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4, col5, col6 = st.columns(6)

    col1.metric("FMP Earnings", stats.get("fmp_earnings_found", 0))
    col2.metric("Finnhub Earnings", stats.get("finnhub_earnings_found", 0))
    col3.metric("TradingView Earnings", stats.get("tradingview_earnings_found", 0))
    col4.metric("Kandidaten gesamt", stats.get("candidates_total", 0))
    col5.metric("Mit Performance-Daten", stats.get("stocks_with_price_data", 0))
    col6.metric("Treffer", hits)

    if stats.get("best_symbol") is not None:
        st.metric(
            "Bester geprüfter Kandidat",
            f"{stats.get('best_company')} ({stats.get('best_symbol')})",
            format_percent(stats.get("best_performance")),
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

        card_class = "stock-card-hit" if status == "Treffer" else "stock-card-watch" if status == "Knapp darunter" else ""

        with st.container():
            st.markdown(
                f"""
                <div class="stock-card {card_class}">
                    <div class="stock-title">{company} ({ticker})</div>
                    <div class="stock-meta">
                        WKN: {wkn} · Börse: {exchange} · Earnings-Datum: {row['Datum']} · Earnings-Quelle: {source}
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

                st.markdown(
                    f"""
                    <div class="badge-row">
                        <span class="badge {status_badge_class(status)}">{status}</span>
                        <span class="badge">{rating_badge(rating)}</span>
                        <span class="badge">{stage2_status}</span>
                        <span class="badge">Rel. SPY: {row['Relativ zu SPY']}</span>
                        <span class="badge">Rel. QQQ: {row['Relativ zu QQQ']}</span>
                        <span class="badge">1M: {row['1M']}</span>
                        <span class="badge">3M: {row['3M']}</span>
                    </div>
                    <div class="info-line">
                        <b>Aktion:</b> {action} · <b>Kursdaten:</b> {data_source}
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
            "Datum",
            "calendar_source",
            "Kurs",
            "2M Proxy",
            "Abstand 50-Tage-Linie",
            "Abstand 200-Tage-Linie",
            "stage2_score",
            "score",
            "status",
            "chart_url",
        ]
    ].rename(
        columns={
            "company": "Unternehmen",
            "symbol": "Ticker",
            "wkn": "WKN",
            "calendar_source": "Earnings-Quelle",
            "stage2_score": "Stage 2",
            "score": "Score",
            "status": "Status",
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
            "earnings_date": "Earnings-Datum roh",
            "calendar_source": "Earnings-Quelle",
            "current_close": "Aktueller Kurs roh",
            "performance_1m_pct": "1M-Performance %",
            "performance_3m_pct": "3M-Performance %",
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
                <b>Treffer:</b> geschätzte 2M-Performance liegt bei mindestens {min_performance:.0f} %.<br>
                <b>2M-Performance Proxy:</b> wird aus TradingView 1M- und 3M-Performance abgeleitet.<br>
                <b>Abstand 50-Tage-Linie:</b> Abstand des aktuellen Kurses zur 50-Tage-Linie.<br>
                <b>Abstand 200-Tage-Linie:</b> Abstand des aktuellen Kurses zur 200-Tage-Linie.<br>
                <b>Earnings-Datum / Earnings-Quelle:</b> zeigt, wann die Zahlen anstehen oder zuletzt gemeldet wurden und aus welcher Quelle der Termin kommt.<br>
                <b>Stage-2-Score:</b> technische Trendqualität über Kurs, 50-Tage-Linie, 200-Tage-Linie und Performance.<br>
                <b>Chart-Vorschau:</b> kleine Finviz-Bildvorschau. Für Detailanalyse immer TradingView öffnen.
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


if not run_now:
    st.info("Klicke links auf **Screener jetzt ausführen**.")
    show_explanation_box(min_performance)
    st.stop()


with st.spinner("Screener läuft. TradingView-Daten werden geladen und gefiltert..."):
    hits_df, all_df, stats = run_screen(
        lookback_days=lookback_days,
        forward_days=forward_days,
        min_performance_2m=min_performance,
        tradingview_limit=tradingview_limit,
    )


if stats.get("tradingview_error"):
    st.warning(f"TradingView-Quelle: {stats['tradingview_error']}")

show_screening_summary(stats)

st.divider()

if all_df.empty:
    st.warning("Keine Kandidaten mit verwertbaren TradingView-Performance-Daten.")
    show_explanation_box(min_performance)
    st.stop()


display_all = prepare_display_df(all_df)
display_hits = prepare_display_df(hits_df)


show_candidate_cards(
    hits_df,
    title="Treffer: Aktien über Momentum-Filter",
    empty_message="Keine Aktie erfüllt aktuell deinen Momentum-Filter.",
    limit=max_cards,
    show_charts=show_chart_previews,
)

st.divider()

st.subheader("Filter für alle Kandidaten")

f1, f2, f3 = st.columns(3)

with f1:
    status_filter = st.multiselect(
        "Status",
        options=sorted(display_all["status"].dropna().unique()),
        default=sorted(display_all["status"].dropna().unique()),
    )

with f2:
    source_filter = st.multiselect(
        "Earnings-Quelle",
        options=sorted(display_all["calendar_source"].dropna().unique()),
        default=sorted(display_all["calendar_source"].dropna().unique()),
    )

with f3:
    stage_filter = st.multiselect(
        "Stage-2-Status",
        options=sorted(display_all["stage2_status"].dropna().unique()),
        default=sorted(display_all["stage2_status"].dropna().unique()),
    )

filtered_all = all_df[
    all_df["status"].isin(status_filter)
    & all_df["calendar_source"].isin(source_filter)
    & all_df["stage2_status"].isin(stage_filter)
]

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
