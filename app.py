import streamlit as st

from screener import analyze_single_symbol, run_screen


st.set_page_config(
    page_title="Earnings Momentum Screener",
    layout="wide",
)

st.title("Earnings Momentum Screener")
st.caption(
    "Earnings-Kandidaten mit 2-Monats-Momentum. Ziel: Aktien finden, die vor den Zahlen bereits institutionelle Stärke zeigen."
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
    help="Prüft nur das Kursmomentum eines einzelnen Tickers, unabhängig vom Earnings-Kalender.",
)

manual_check = st.sidebar.button("Ticker prüfen")


def rename_columns(df):
    return df.rename(
        columns={
            "symbol": "Ticker",
            "company": "Unternehmen",
            "wkn": "WKN",
            "isin": "ISIN",
            "earnings_date": "Earnings-Datum",
            "current_close": "Aktueller Kurs",
            "performance_2m_pct": "2M-Performance %",
            "above_sma_20": "Über 20-Tage-Linie",
            "above_sma_50": "Über 50-Tage-Linie",
            "distance_sma_50_pct": "Abstand 50-Tage-Linie %",
            "score": "Score",
            "rating": "Rating",
            "status": "Status",
            "interpretation": "Interpretation",
            "action": "Aktion",
            "chart_url": "Chart öffnen",
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
            "Earnings-Datum",
            "2M-Performance %",
            "Aktueller Kurs",
            "Score",
            "Rating",
            "Status",
            "Aktion",
            "Chart öffnen",
            "Interpretation",
            "Über 20-Tage-Linie",
            "Über 50-Tage-Linie",
            "Abstand 50-Tage-Linie %",
        ],
        column_config={
            "2M-Performance %": st.column_config.NumberColumn(
                "2M-Performance %",
                format="%.2f %%",
            ),
            "Aktueller Kurs": st.column_config.NumberColumn(
                "Aktueller Kurs",
                format="%.2f",
            ),
            "Score": st.column_config.ProgressColumn(
                "Score",
                min_value=0,
                max_value=100,
            ),
            "Chart öffnen": st.column_config.LinkColumn(
                "Chart öffnen",
                display_text="TradingView",
            ),
        },
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
        col5.metric("Status", row["status"])

        st.info(row["interpretation"])

        show_table(rename_columns(manual_df))

    st.stop()

if not run_now:
    st.info("Klicke links auf **Screener jetzt ausführen**, um aktuelle Earnings-Kandidaten zu laden.")
    st.stop()

with st.spinner("Screener läuft. Earnings-Kalender und Kursdaten werden geladen..."):
    hits_df, all_df, stats = run_screen(
        lookback_days=lookback_days,
        forward_days=forward_days,
        min_performance_2m=min_performance,
    )

st.subheader("Kurzfazit")

if stats["hits"] > 0:
    st.success(
        f"{stats['hits']} Aktie(n) erfüllen den Momentum-Filter von mindestens {stats['min_performance_2m']:.0f} %. "
        "Das sind die Kandidaten für eine Detailanalyse."
    )
else:
    if stats["best_symbol"] is not None:
        st.warning(
            f"Kein Treffer über {stats['min_performance_2m']:.0f} %. "
            f"Bester Kandidat ist {stats['best_symbol']} mit {stats['best_performance']:.2f} %. "
            "Das ist aktuell kein starkes Earnings-Momentum-Setup."
        )
    else:
        st.error(
            "Es wurden keine verwertbaren Kandidaten gefunden. Entweder liefert der Earnings-Kalender wenig Daten "
            "oder es fehlen Kursdaten."
        )

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Earnings gefunden", stats["earnings_found"])
col2.metric("Mit Kursdaten geprüft", stats["stocks_with_price_data"])
col3.metric("Treffer", stats["hits"])
col4.metric("Momentum-Filter", f">{stats['min_performance_2m']:.0f} %")

if stats["best_symbol"] is not None:
    col5.metric(
        "Bestes Momentum",
        f"{stats['best_symbol']} {stats['best_performance']:.2f} %",
    )
else:
    col5.metric("Bestes Momentum", "n/a")

st.caption(
    f"Zeitraum: {stats['start_date']} bis {stats['end_date']} · "
    f"Ohne Kursdaten/zu wenig Historie: {stats['skipped_no_prices']}"
)

st.divider()

if all_df.empty:
    st.warning("Es wurden keine Aktien mit ausreichenden Kursdaten geprüft.")
    st.stop()

display_all = rename_columns(all_df)
display_hits = rename_columns(hits_df)

st.subheader("Treffer: Aktien über Momentum-Filter")

if display_hits.empty:
    st.warning("Keine Aktie erfüllt aktuell deinen Momentum-Filter. Kein A-Setup vorhanden.")
else:
    show_table(display_hits)

st.divider()

st.subheader("Alle geprüften Kandidaten — sortiert nach Momentum")

status_filter = st.multiselect(
    "Status filtern",
    options=sorted(display_all["Status"].unique()),
    default=sorted(display_all["Status"].unique()),
)

filtered_all = display_all[display_all["Status"].isin(status_filter)]

show_table(filtered_all)

st.subheader("Momentum-Ranking")

top15 = filtered_all.sort_values("2M-Performance %", ascending=False).head(15)

st.bar_chart(
    top15,
    x="Ticker",
    y="2M-Performance %",
)

st.divider()

st.subheader("Wie du das Ergebnis lesen musst")

st.markdown(
    """
**Treffer** bedeutet: Die Aktie hat vor oder rund um die Quartalszahlen mindestens deinen eingestellten Momentum-Wert erreicht.

**Knapp darunter** bedeutet: Die Aktie ist nahe am Filter, aber noch kein starkes Setup.

**Unter Filter** bedeutet: Die Aktie berichtet zwar Zahlen, aber der Kurs zeigt nicht genug Vorstärke.

**Chart öffnen** führt direkt zu TradingView. Dort kannst du den Kursverlauf visuell prüfen.

**WKN** wird nur angezeigt, wenn sie in der lokalen Mapping-Liste hinterlegt ist. FMP liefert WKN nicht zuverlässig automatisch.
"""
)

st.caption(
    "Keine Anlageberatung. Der Screener zeigt Kandidaten mit Kursmomentum rund um Quartalszahlen. "
    "Bei stark gelaufenen Aktien sind hohe Erwartungen oft bereits eingepreist."
)
