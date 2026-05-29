import streamlit as st

from screener import run_screen


st.set_page_config(
    page_title="Earnings Momentum Screener",
    layout="wide",
)

st.title("Earnings Momentum Screener")
st.caption(
    "Quartalszahlen im gewählten Zeitraum + 2-Monats-Momentum + technischer Trendfilter."
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
    "Mindestperformance 2 Monate",
    min_value=0.0,
    max_value=50.0,
    value=15.0,
    step=1.0,
)

run_now = st.sidebar.button("Screener jetzt ausführen")

if not run_now:
    st.info("Klicke links auf **Screener jetzt ausführen**, um aktuelle Daten zu laden.")
    st.stop()

with st.spinner("Screener läuft. Earnings-Kalender und Kursdaten werden geladen..."):
    hits_df, all_df, stats = run_screen(
        lookback_days=lookback_days,
        forward_days=forward_days,
        min_performance_2m=min_performance,
    )

st.subheader("Screening-Status")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Earnings gefunden", stats["earnings_found"])
col2.metric("Mit Kursdaten geprüft", stats["stocks_with_price_data"])
col3.metric("Treffer", stats["hits"])
col4.metric("Filter", f">{stats['min_performance_2m']:.0f} %")

st.caption(
    f"Zeitraum: {stats['start_date']} bis {stats['end_date']} · "
    f"Ohne Kursdaten/zu wenig Historie: {stats['skipped_no_prices']}"
)

st.divider()

if all_df.empty:
    st.warning("Es wurden keine Aktien mit ausreichenden Kursdaten geprüft.")
    st.stop()

st.subheader("Treffer über Momentum-Filter")

if hits_df.empty:
    st.warning("Keine Aktien über dem aktuellen Momentum-Filter.")
else:
    st.dataframe(
        hits_df,
        width="stretch",
        hide_index=True,
    )

st.divider()

st.subheader("Alle geprüften Earnings-Kandidaten nach 2-Monats-Momentum")

status_filter = st.multiselect(
    "Status filtern",
    options=sorted(all_df["status"].unique()),
    default=sorted(all_df["status"].unique()),
)

filtered_all = all_df[all_df["status"].isin(status_filter)]

st.dataframe(
    filtered_all,
    width="stretch",
    hide_index=True,
)

st.subheader("Top 15 Momentum-Kandidaten")

top15 = filtered_all.sort_values("performance_2m_pct", ascending=False).head(15)

st.bar_chart(
    top15,
    x="symbol",
    y="performance_2m_pct",
)

st.divider()

st.caption(
    "Keine Anlageberatung. Der Screener zeigt Kandidaten mit Kursmomentum rund um Quartalszahlen. "
    "Bei stark gelaufenen Aktien sind hohe Erwartungen oft bereits eingepreist."
)
