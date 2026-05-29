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
            background: #0E1117;
            color: #E6EAF2;
        }

        [data-testid="stSidebar"] {
            background: #111827;
            border-right: 1px solid rgba(255,255,255,0.08);
        }

        [data-testid="stSidebar"] * {
            color: #E6EAF2;
        }

        h1, h2, h3, h4 {
            color: #F5F7FA !important;
            letter-spacing: -0.02em;
        }

        p, span, div {
            color: inherit;
        }

        .block-container {
            padding-top: 2.2rem;
            padding-left: 2.2rem;
            padding-right: 2.2rem;
            max-width: 1550px;
        }

        .main-header {
            padding: 18px 22px;
            border-radius: 22px;
            background: linear-gradient(135deg, #141A24 0%, #1B2432 100%);
            border: 1px solid rgba(255,255,255,0.08);
            box-shadow: 0 10px 28px rgba(0,0,0,0.35);
            margin-bottom: 22px;
        }

        .main-title {
            font-size: 36px;
            font-weight: 800;
            line-height: 1.1;
            margin-bottom: 6px;
            color: #F8FAFC;
        }

        .main-subtitle {
            font-size: 14px;
            color: #AAB4C3;
        }

        .section-card {
            background: #141A24;
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 20px;
            padding: 18px 20px;
            box-shadow: 0 8px 22px rgba(0,0,0,0.28);
            margin-bottom: 18px;
        }

        .stock-card {
            background: #141A24;
            border: 1px solid rgba(255,255,255,0.09);
            border-radius: 22px;
            padding: 16px 18px 18px 18px;
            margin-bottom: 16px;
            box-shadow: 0 10px 26px rgba(0,0,0,0.30);
        }

        .stock-card-hit {
            border-color: rgba(34,197,94,0.55);
            box-shadow: 0 0 0 1px rgba(34,197,94,0.16), 0 10px 26px rgba(0,0,0,0.30);
        }

        .stock-card-watch {
            border-color: rgba(234,179,8,0.45);
        }

        .stock-title {
            font-size: 21px;
            font-weight: 800;
            color: #F8FAFC;
            margin-bottom: 4px;
        }

        .stock-meta {
            color: #97A3B6;
            font-size: 12px;
            margin-bottom: 12px;
        }

        .metric-box {
            background: #0F1623;
            border: 1px solid rgba(255,255,255,0.075);
            border-radius: 16px;
            padding: 11px 12px;
            height: 78px;
        }

        .metric-label {
            font-size: 11px;
            color: #93A0B4;
            margin-bottom: 5px;
            white-space: nowrap;
        }

        .metric-value {
            font-size: 22px;
            line-height: 1.1;
            font-weight: 800;
            color: #F8FAFC;
            white-space: nowrap;
        }

        .metric-value-small {
            font-size: 18px;
            line-height: 1.15;
            font-weight: 800;
            color: #F8FAFC;
            white-space: nowrap;
        }

        .positive {
            color: #22C55E !important;
        }

        .negative {
            color: #EF4444 !important;
        }

        .neutral {
            color: #F59E0B !important;
        }

        .muted {
            color: #93A0B4 !important;
        }

        .badge-row {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 10px;
            margin-bottom: 8px;
        }

        .badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            border-radius: 999px;
            padding: 5px 10px;
            font-size: 12px;
            font-weight: 700;
            border: 1px solid rgba(255,255,255,0.10);
            background: #0F1623;
            color: #DDE3EC;
        }

        .badge-green {
            background: rgba(34,197,94,0.13);
            border-color: rgba(34,197,94,0.38);
            color: #86EFAC;
        }

        .badge-yellow {
            background: rgba(245,158,11,0.13);
            border-color: rgba(245,158,11,0.38);
            color: #FCD34D;
        }

        .badge-red {
            background: rgba(239,68,68,0.13);
            border-color: rgba(239,68,68,0.38);
            color: #FCA5A5;
        }

        .badge-blue {
            background: rgba(59,130,246,0.13);
            border-color: rgba(59,130,246,0.38);
            color: #93C5FD;
        }

        .info-line {
            color: #AAB4C3;
            font-size: 13px;
            line-height: 1.45;
            margin-top: 8px;
        }

        .chart-wrap {
            background: #0B0F17;
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 16px;
            overflow: hidden;
            padding: 8px;
            margin-top: 8px;
        }

        .chart-wrap img {
            width: 100%;
            max-width: 560px;
            height: auto;
            display: block;
            border-radius: 10px;
        }

        .chart-caption {
            font-size: 11px;
            color: #8C98AA;
            margin-top: 5px;
        }

        .stButton > button,
        .stLinkButton > a {
            background: #2563EB !important;
            color: white !important;
            border: 1px solid rgba(255,255,255,0.10) !important;
            border-radius: 12px !important;
            font-weight: 800 !important;
            box-shadow: 0 6px 16px rgba(37,99,235,0.25);
        }

        .stButton > button:hover,
        .stLinkButton > a:hover {
            background: #1D4ED8 !important;
            color: white !important;
            border-color: rgba(255,255,255,0.18) !important;
        }

        div[data-testid="stMetric"] {
            background: #141A24;
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 16px;
            padding: 13px 14px;
            box-shadow: 0 6px 16px rgba(0,0,0,0.20);
        }

        div[data-testid="stMetricLabel"] {
            color: #93A0B4 !important;
        }

        div[data-testid="stMetricValue"] {
            color: #F8FAFC !important;
        }

        .stAlert {
            border-radius: 16px;
        }

        [data-testid="stDataFrame"] {
            background: #141A24;
            border-radius: 16px;
            overflow: hidden;
        }

        hr {
            border-color: rgba(255,255,255,0.08);
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
            Schwarzes Analysten-Dashboard · TradingView als Hauptquelle · FMP/Finnhub ergänzen Earnings-Termine
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
                        WKN: {wkn} · Börse: {exchange} · Earnings: {row['Datum']} · Quelle: {source}
                    </div>
                """,
                unsafe_allow_html=True,
            )

            top_left, top_right = st.columns([2.1, 1])

            with top_left:
                c1, c2, c3 = st.columns(3)

                with c1:
                    st.markdown(
                        metric_box("Aktueller Kurs", row["Kurs"]),
                        unsafe_allow_html=True,
                    )

                with c2:
                    st.markdown(
                        metric_box(
                            "2M Proxy",
                            row["2M Proxy"],
                            numeric_class(row.get("performance_2m_proxy_pct")),
                        ),
                        unsafe_allow_html=True,
                    )

                with c3:
                    st.markdown(
                        metric_box("Gesamtscore", f"{int(row['score'])} %"),
                        unsafe_allow_html=True,
                    )

                c4, c5, c6 = st.columns(3)

                with c4:
                    st.markdown(
                        metric_box_small(
                            "Abstand 50-Tage-Linie",
                            row["Abstand 50-Tage-Linie"],
                            numeric_class(row.get("distance_sma_50_pct")),
                        ),
                        unsafe_allow_html=True,
                    )

                with c5:
                    st.markdown(
                        metric_box_small(
                            "Abstand 200-Tage-Linie",
                            row["Abstand 200-Tage-Linie"],
                            numeric_class(row.get("distance_sma_200_pct")),
                        ),
                        unsafe_allow_html=True,
                    )

                with c6:
                    st.markdown(
                        metric_box_small("Stage 2", f"{int(row['stage2_score'])} %"),
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

            with top_right:
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
        <div class="section-card">
            <h3>Lesart</h3>
            <div class="info-line">
                <b>Treffer:</b> geschätzte 2M-Performance liegt bei mindestens {min_performance:.0f} %.<br>
                <b>2M-Performance Proxy:</b> wird aus TradingView 1M- und 3M-Performance abgeleitet.<br>
                <b>Abstand 50-Tage-Linie:</b> Abstand des aktuellen Kurses zur 50-Tage-Linie.<br>
                <b>Abstand 200-Tage-Linie:</b> Abstand des aktuellen Kurses zur 200-Tage-Linie.<br>
                <b>Relativ zu SPY / QQQ:</b> Aktie läuft stärker oder schwächer als Markt/Tech.<br>
                <b>Stage-2-Score:</b> technische Trendqualität über Kurs, 50-Tage-Linie, 200-Tage-Linie und Performance.<br>
                <b>Chart-Vorschau:</b> kleine Finviz-Bildvorschau. Für Detailanalyse immer den TradingView-Link öffnen.
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


st.subheader("Marktumfeld")
show_market_regime(stats)

st.divider()

st.subheader("Kurzfazit")

if stats["tradingview_error"]:
    st.warning(f"TradingView-Quelle: {stats['tradingview_error']}")

if stats["hits"] > 0:
    st.success(
        f"{stats['hits']} Aktie(n) erfüllen den Momentum-Filter von mindestens "
        f"{stats['min_performance_2m']:.0f} %."
    )
else:
    if stats["best_symbol"] is not None:
        st.warning(
            f"Kein Treffer über {stats['min_performance_2m']:.0f} %. "
            f"Bester geprüfter Kandidat: {stats['best_company']} ({stats['best_symbol']}) "
            f"mit {format_percent(stats['best_performance'])}."
        )
    else:
        st.error("Keine verwertbaren Kandidaten gefunden.")


col1, col2, col3, col4, col5, col6 = st.columns(6)

col1.metric("FMP Earnings", stats["fmp_earnings_found"])
col2.metric("Finnhub Earnings", stats["finnhub_earnings_found"])
col3.metric("TradingView Earnings", stats["tradingview_earnings_found"])
col4.metric("Kandidaten gesamt", stats["candidates_total"])
col5.metric("Mit Performance-Daten", stats["stocks_with_price_data"])
col6.metric("Treffer", stats["hits"])

st.metric("Momentum-Filter", f">{stats['min_performance_2m']:.0f} %")

if stats["best_symbol"] is not None:
    st.metric(
        "Bester geprüfter Kandidat",
        f"{stats['best_company']} ({stats['best_symbol']})",
        format_percent(stats["best_performance"]),
    )

st.caption(
    f"Zeitraum: {format_date_de(stats['start_date'])} bis {format_date_de(stats['end_date'])}"
)

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
