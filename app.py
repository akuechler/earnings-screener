import pandas as pd
import streamlit as st

from screener import analyze_single_symbol, run_screen


st.set_page_config(
    page_title="Earnings Momentum Screener von Andreas",
    layout="wide",
)

st.title("Earnings Momentum Screener von Andreas")
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
    help="Höher = mehr Aktienuniversum.",
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
        return f"{float(value):.2f} %"
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


def prepare_display_df(df):
    if df is None or df.empty:
        return pd.DataFrame()

    display = df.copy()

    display["Datum"] = display["earnings_date"].apply(format_date_de)
    display["Kurs"] = display["current_close"].apply(format_currency)
    display["2M"] = display["performance_2m_proxy_pct"].apply(format_percent)
    display["1M"] = display["performance_1m_pct"].apply(format_percent)
    display["3M"] = display["performance_3m_pct"].apply(format_percent)
    display["Rel. SPY"] = display["spy_relative_proxy_pct"].apply(format_percent)
    display["Rel. QQQ"] = display["qqq_relative_proxy_pct"].apply(format_percent)
    display["Abstand 50T"] = display["distance_sma_50_pct"].apply(format_percent)
    display["Abstand 200T"] = display["distance_sma_200_pct"].apply(format_percent)
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


def show_candidate_cards(df, title, empty_message, limit=30):
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
            header_left, header_right = st.columns([3, 1])

            with header_left:
                st.markdown(
                    f"### {company} ({ticker})"
                )
                st.caption(
                    f"WKN: {wkn} · Börse: {exchange} · Earnings: {row['Datum']} · Quelle: {source}"
                )

            with header_right:
                if chart_url:
                    st.link_button("Chart öffnen", chart_url, use_container_width=True)

            k1, k2, k3, k4, k5, k6 = st.columns(6)

            k1.metric("Aktueller Kurs", row["Kurs"])
            k2.metric("2M Proxy", row["2M"])
            k3.metric("Abstand 50T", row["Abstand 50T"])
            k4.metric("Abstand 200T", row["Abstand 200T"])
            k5.metric("Stage-2", f"{int(row['stage2_score'])} %")
            k6.metric("Score", f"{int(row['score'])} %")

            c1, c2, c3, c4 = st.columns(4)

            c1.write(f"**Status:** {row['Statusanzeige']}")
            c2.write(f"**Rating:** {row['Ratinganzeige']}")
            c3.write(f"**Rel. SPY:** {row['Rel. SPY']}")
            c4.write(f"**Rel. QQQ:** {row['Rel. QQQ']}")

            st.caption(f"Aktion: {action} · Kursdaten: {data_source}")

            if interpretation:
                st.info(interpretation)


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
            "2M",
            "Abstand 50 Tage Linie",
            "Abstand 200 Tage Linie",
            "stage2_score",
            "score",
            "Statusanzeige",
        ]
    ].rename(
        columns={
            "company": "Unternehmen",
            "symbol": "Ticker",
            "wkn": "WKN",
            "stage2_score": "Stage-2",
            "score": "Score",
            "Statusanzeige": "Status",
        }
    )

    st.dataframe(
        compact,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Stage-2": st.column_config.ProgressColumn(
                "Stage-2",
                min_value=0,
                max_value=100,
            ),
            "Score": st.column_config.ProgressColumn(
                "Score",
                min_value=0,
                max_value=100,
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
### Lesart

- **Treffer**: geschätzte 2M-Performance liegt bei mindestens **{min_performance:.0f} %**.
- **2M-Performance Proxy**: wird aus TradingView 1M- und 3M-Performance abgeleitet.
- **Abstand 50T / 200T**: Abstand des aktuellen Kurses zur 50- bzw. 200-Tage-Linie.
- **Relativ zu SPY / QQQ**: Aktie läuft stärker oder schwächer als Markt/Tech.
- **Stage-2-Score**: technische Trendqualität über Kurs, SMA50, SMA200 und Performance.
- **Wichtig**: Treffer sind Kandidaten für Detailanalyse, keine Kaufempfehlung.
"""
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
    limit=20,
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
