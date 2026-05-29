import streamlit as st

from screener import analyze_single_symbol, run_screen


st.set_page_config(
    page_title="Earnings Momentum Screener",
    layout="wide",
)

st.title("Earnings Momentum Screener")
st.caption(
    "Universe-basierter Earnings-Momentum-Screener aus FMP + Finnhub + TradingView "
    "mit Relative Strength, Stage-2-Score und Marktampel."
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
    help="Standard: 15 %. Du kannst den Filter frei anpassen.",
)

run_now = st.sidebar.button("Screener jetzt ausführen")

st.sidebar.divider()

manual_symbol = st.sidebar.text_input(
    "Ticker manuell prüfen",
    value="DELL",
    help="Prüft nur das Kursmomentum eines einzelnen Tickers.",
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
            "performance_2m_pct": "2M-Performance %",
            "spy_relative_2m_pct": "Relativ zu SPY %",
            "qqq_relative_2m_pct": "Relativ zu QQQ %",
            "above_sma_20": "Über 20-Tage-Linie",
            "above_sma_50": "Über 50-Tage-Linie",
            "above_sma_150": "Über 150-Tage-Linie",
            "above_sma_200": "Über 200-Tage-Linie",
            "distance_sma_50_pct": "Abstand 50-Tage-Linie %",
            "stage2_score": "Stage-2-Score",
            "stage2_status": "Stage-2-Status",
            "score": "Gesamtscore",
            "rating": "Rating",
            "status": "Status",
            "interpretation": "Interpretation",
            "action": "Aktion",
            "chart_url": "Chart öffnen",
            "data_source": "Kursdatenquelle",
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
            "2M-Performance %",
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
            "Kursdatenquelle",
            "Über 20-Tage-Linie",
            "Über 50-Tage-Linie",
            "Über 150-Tage-Linie",
            "Über 200-Tage-Linie",
            "Abstand 50-Tage-Linie %",
        ],
        column_config={
            "2M-Performance %": st.column_config.NumberColumn(
                "2M-Performance %",
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
            "Abstand 50-Tage-Linie %": st.column_config.NumberColumn(
                "Abstand 50-Tage-Linie %",
                format="%.2f %%",
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

    if not market:
        st.warning("Marktampel konnte nicht berechnet werden.")
        return

    regime = market.get("regime", "unbekannt")
    interpretation = market.get("interpretation", "")

    if regime == "grün":
        st.success(f"Marktampel: GRÜN — {interpretation}")
    elif regime == "neutral":
        st.warning(f"Marktampel: NEUTRAL — {interpretation}")
    elif regime == "rot":
        st.error(f"Marktampel: ROT — {interpretation}")
    else:
        st.info("Marktampel: unbekannt")

    spy = market.get("spy_status", {})
    qqq = market.get("qqq_status", {})

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("SPY Status", spy.get("status", "n/a"))
    col2.metric(
        "SPY 2M",
        f"{spy.get('perf_2m'):.2f} %" if spy.get("perf_2m") is not None else "n/a",
    )
    col3.metric("QQQ Status", qqq.get("status", "n/a"))
    col4.metric(
        "QQQ 2M",
        f"{qqq.get('perf_2m'):.2f} %" if qqq.get("perf_2m") is not None else "n/a",
    )


def show_explanation_box(min_performance):
    st.markdown(
        f"""
### Lesart des Screeners

- **Treffer**: Aktie liegt bei mindestens **{min_performance:.0f} %** 2-Monats-Performance.
- **Relativ zu SPY / QQQ**: zeigt, ob die Aktie den Gesamtmarkt oder den Tech-Index schlägt.
- **Stage-2-Score**: technische Trendqualität nach Minervini/Weinstein-Logik.
- **Stage 2 stark**: Kurs über wichtigen gleitenden Durchschnitten, 200-Tage-Linie steigt, Nähe zum Hoch, Abstand zum Tief.
- **Gesamtscore**: Mischung aus Momentum, Trend, relativer Stärke und Stage-2-Qualität.
- **Marktampel**: prüft SPY und QQQ. Bei roter Ampel sind Earnings-Breakouts riskanter.
- **Chart öffnen** öffnet den TradingView-Chart zur visuellen Prüfung.
- **WKN** wird angezeigt, wenn sie in der lokalen Mapping-Liste hinterlegt ist.
"""
    )


if manual_check:
    st.subheader(f"Manuelle Momentum-Prüfung: {manual_symbol.upper()}")

    with st.spinner("Ticker wird geprüft..."):
        manual_df = analyze_single_symbol(
            symbol=manual_symbol,
            min_performance_2m=min_performance,
        )

    if manual_df is None or manual_df.empty:
        st.error("Für diesen Ticker konnten keine ausreichenden Kursdaten geladen werden.")
    else:
        row = manual_df.iloc[0]

        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Unternehmen", row["company"])
        col2.metric("Ticker", row["symbol"])
        col3.metric("WKN", row["wkn"])
        col4.metric("2M-Performance", f"{row['performance_2m_pct']:.2f} %")
        col5.metric("Stage-2-Score", int(row["stage2_score"]))

        if row["status"] == "Treffer":
            st.success(row["interpretation"])
        elif row["status"] == "Knapp darunter":
            st.warning(row["interpretation"])
        else:
            st.info(row["interpretation"])

        show_table(rename_columns(manual_df))

    st.stop()


if not run_now:
    st.info(
        "Klicke links auf **Screener jetzt ausführen**, um alle Earnings-Kandidaten "
        "aus FMP + Finnhub + TradingView zu laden."
    )
    show_explanation_box(min_performance)
    st.stop()


with st.spinner(
    "Screener läuft. Earnings-Kalender, Kursdaten, Relative Strength, Stage-2-Score und Marktampel werden geladen..."
):
    hits_df, all_df, stats = run_screen(
        lookback_days=lookback_days,
        forward_days=forward_days,
        min_performance_2m=min_performance,
    )


st.subheader("Marktumfeld")

show_market_regime(stats)

st.divider()


st.subheader("Kurzfazit")

if stats["tradingview_error"]:
    st.warning(f"TradingView-Quelle konnte nicht geladen werden: {stats['tradingview_error']}")

if stats["hits"] > 0:
    st.success(
        f"{stats['hits']} Aktie(n) erfüllen den Momentum-Filter von mindestens "
        f"{stats['min_performance_2m']:.0f} %. "
        "Das sind Kandidaten für eine Detailanalyse."
    )
else:
    if stats["best_symbol"] is not None:
        st.warning(
            f"Kein Treffer über {stats['min_performance_2m']:.0f} %. "
            f"Bester Kandidat ist {stats['best_company']} ({stats['best_symbol']}) "
            f"mit {stats['best_performance']:.2f} %. "
            "Das ist aktuell kein starkes Earnings-Momentum-Setup."
        )
    else:
        st.error(
            "Es wurden keine verwertbaren Kandidaten gefunden. "
            "Entweder liefern die Kalender keine Daten oder es fehlen Kursdaten."
        )


col1, col2, col3, col4, col5, col6 = st.columns(6)

col1.metric("FMP Earnings", stats["fmp_earnings_found"])
col2.metric("Finnhub Earnings", stats["finnhub_earnings_found"])
col3.metric("TradingView Earnings", stats["tradingview_earnings_found"])
col4.metric("Kandidaten gesamt", stats["candidates_total"])
col5.metric("Mit Kursdaten geprüft", stats["stocks_with_price_data"])
col6.metric("Treffer", stats["hits"])

st.metric("Momentum-Filter", f">{stats['min_performance_2m']:.0f} %")

if stats["best_symbol"] is not None:
    st.metric(
        "Bestes Setup",
        f"{stats['best_company']} ({stats['best_symbol']})",
        f"{stats['best_performance']:.2f} %",
    )

st.caption(
    f"Zeitraum: {stats['start_date']} bis {stats['end_date']} · "
    f"Ohne Kursdaten/zu wenig Historie: {stats['skipped_no_prices']}"
)

st.divider()


if all_df.empty:
    st.warning("Es wurden keine Aktien mit ausreichenden Kursdaten geprüft.")
    show_explanation_box(min_performance)
    st.stop()


display_all = rename_columns(all_df)
display_hits = rename_columns(hits_df)


st.subheader("Treffer: Aktien über Momentum-Filter")

if display_hits.empty:
    st.warning("Keine Aktie erfüllt aktuell deinen Momentum-Filter. Kein A-Setup vorhanden.")
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

top15 = filtered_all.sort_values("Gesamtscore", ascending=False).head(15)

st.bar_chart(
    top15,
    x="Ticker",
    y="Gesamtscore",
)


st.subheader("Top 15 nach 2M-Performance")

top15_momentum = filtered_all.sort_values("2M-Performance %", ascending=False).head(15)

st.bar_chart(
    top15_momentum,
    x="Ticker",
    y="2M-Performance %",
)


st.divider()

show_explanation_box(min_performance)

st.caption(
    "Keine Anlageberatung. Der Screener zeigt Kandidaten mit Kursmomentum rund um Quartalszahlen. "
    "Bei stark gelaufenen Aktien sind hohe Erwartungen oft bereits eingepreist."
)
