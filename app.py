import streamlit as st

from screener import analyze_single_symbol, run_screen


st.set_page_config(
    page_title="Earnings Momentum Screener",
    layout="wide",
)

st.title("Earnings Momentum Screener")
st.caption(
    "TradingView-basierter Earnings-Momentum-Screener. "
    "TradingView ist jetzt die Hauptquelle. FMP/Finnhub ergänzen nur noch Earnings-Termine."
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
    help="Höher = mehr Aktienuniversum. Läuft trotzdem schnell, weil keine Kursdaten einzeln nachgeladen werden.",
)

run_now = st.sidebar.button("Screener jetzt ausführen")

st.sidebar.divider()

manual_symbol = st.sidebar.text_input(
    "Ticker manuell prüfen",
    value="DELL",
)

manual_check = st.sidebar.button("Ticker prüfen")


def rename_columns(df):
    return df.rename(
        columns={
            "symbol": "Ticker",
            "company": "Unternehmen",
            "wkn": "WKN",
            "isin": "ISIN",
            "exchange": "Börse",
            "earnings_date": "Earnings-Datum",
            "calendar_source": "Earnings-Quelle",
            "current_close": "Aktueller Kurs",
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


def show_table(df):
    st.dataframe(
        df,
        width="stretch",
        hide_index=True,
        column_order=[
            "Unternehmen",
            "Ticker",
            "WKN",
            "ISIN",
            "Börse",
            "Earnings-Datum",
            "Earnings-Quelle",
            "2M-Performance Proxy %",
            "1M-Performance %",
            "3M-Performance %",
            "Relativ zu SPY %",
            "Relativ zu QQQ %",
            "Stage-2-Score",
            "Stage-2-Status",
            "Gesamtscore",
            "Rating",
            "Status",
            "Aktion",
            "Chart öffnen",
            "Interpretation",
            "Aktueller Kurs",
            "Datenquelle",
            "Über 50-Tage-Linie",
            "Über 200-Tage-Linie",
            "Abstand 50-Tage-Linie %",
            "Abstand 200-Tage-Linie %",
        ],
        column_config={
            "2M-Performance Proxy %": st.column_config.NumberColumn(
                "2M-Performance Proxy %",
                format="%.2f %%",
            ),
            "1M-Performance %": st.column_config.NumberColumn(
                "1M-Performance %",
                format="%.2f %%",
            ),
            "3M-Performance %": st.column_config.NumberColumn(
                "3M-Performance %",
                format="%.2f %%",
            ),
            "Relativ zu SPY %": st.column_config.NumberColumn(
                "Relativ zu SPY %",
                format="%.2f %%",
            ),
            "Relativ zu QQQ %": st.column_config.NumberColumn(
                "Relativ zu QQQ %",
                format="%.2f %%",
            ),
            "Aktueller Kurs": st.column_config.NumberColumn(
                "Aktueller Kurs",
                format="%.2f",
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
            "Chart öffnen": st.column_config.LinkColumn(
                "Chart öffnen",
                display_text="TradingView öffnen",
            ),
        },
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

    col1.metric("SPY 2M Proxy", f"{spy_perf:.2f} %" if spy_perf is not None else "n/a")
    col2.metric("QQQ 2M Proxy", f"{qqq_perf:.2f} %" if qqq_perf is not None else "n/a")


def show_explanation_box(min_performance):
    st.markdown(
        f"""
### Lesart

- **Treffer**: geschätzte 2M-Performance liegt bei mindestens **{min_performance:.0f} %**.
- **2M-Performance Proxy**: wird aus TradingView 1M- und 3M-Performance abgeleitet.
- **Relativ zu SPY / QQQ**: Aktie läuft stärker oder schwächer als Markt/Tech.
- **Stage-2-Score**: Trendqualität über Kurs, SMA50, SMA200 und Performance.
- **Wichtig**: Diese Version ist schnell, weil sie TradingView-Daten direkt nutzt und nicht hunderte Einzelkursdaten lädt.
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
        row = manual_df.iloc[0]

        col1, col2, col3, col4, col5 = st.columns(5)

        col1.metric("Unternehmen", row["company"])
        col2.metric("Ticker", row["symbol"])
        col3.metric("WKN", row["wkn"])
        col4.metric("2M Proxy", f"{row['performance_2m_proxy_pct']:.2f} %")
        col5.metric("Status", row["status"])

        if row["status"] == "Treffer":
            st.success(row["interpretation"])
        elif row["status"] == "Knapp darunter":
            st.warning(row["interpretation"])
        else:
            st.info(row["interpretation"])

        show_table(rename_columns(manual_df))

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
            f"mit {stats['best_performance']:.2f} %."
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
        "Bestes Setup",
        f"{stats['best_company']} ({stats['best_symbol']})",
        f"{stats['best_performance']:.2f} %",
    )

st.caption(
    f"Zeitraum: {stats['start_date']} bis {stats['end_date']}"
)

st.divider()

if all_df.empty:
    st.warning("Keine Kandidaten mit verwertbaren TradingView-Performance-Daten.")
    show_explanation_box(min_performance)
    st.stop()


display_all = rename_columns(all_df)
display_hits = rename_columns(hits_df)


st.subheader("Treffer: Aktien über Momentum-Filter")

if display_hits.empty:
    st.warning("Keine Aktie erfüllt aktuell deinen Momentum-Filter.")
else:
    show_table(display_hits)


st.divider()

st.subheader("Alle geprüften Kandidaten — sortiert nach Gesamtscore")

status_filter = st.multiselect(
    "Status filtern",
    options=sorted(display_all["Status"].unique()),
    default=sorted(display_all["Status"].unique()),
)

source_filter = st.multiselect(
    "Earnings-Quelle filtern",
    options=sorted(display_all["Earnings-Quelle"].unique()),
    default=sorted(display_all["Earnings-Quelle"].unique()),
)

stage_filter = st.multiselect(
    "Stage-2-Status filtern",
    options=sorted(display_all["Stage-2-Status"].unique()),
    default=sorted(display_all["Stage-2-Status"].unique()),
)

filtered_all = display_all[
    display_all["Status"].isin(status_filter)
    & display_all["Earnings-Quelle"].isin(source_filter)
    & display_all["Stage-2-Status"].isin(stage_filter)
]

show_table(filtered_all)


st.subheader("Top 15 nach Gesamtscore")

top15_score = filtered_all.sort_values("Gesamtscore", ascending=False).head(15)

st.bar_chart(
    top15_score,
    x="Ticker",
    y="Gesamtscore",
)


st.subheader("Top 15 nach 2M-Performance Proxy")

top15_momentum = filtered_all.sort_values(
    "2M-Performance Proxy %",
    ascending=False,
).head(15)

st.bar_chart(
    top15_momentum,
    x="Ticker",
    y="2M-Performance Proxy %",
)


st.divider()

show_explanation_box(min_performance)

st.caption(
    "Keine Anlageberatung. TradingView-Daten dienen als Screening-Grundlage. "
    "Treffer müssen manuell im Chart und fundamental geprüft werden."
)
