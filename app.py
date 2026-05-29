import os

import pandas as pd
import streamlit as st

from screener import run_screen


st.set_page_config(
    page_title="Earnings Momentum Screener",
    layout="wide",
)

st.title("Earnings Momentum Screener")
st.caption(
    "Automatisches Screening: Quartalszahlen in den nächsten 7 Tagen "
    "+ Kursanstieg der letzten ca. 42 Handelstage größer als 15 %."
)

st.sidebar.header("Steuerung")

run_now = st.sidebar.button("Screener jetzt ausführen")

data_file = "data/earnings_momentum_screen.csv"

if run_now or not os.path.exists(data_file):
    with st.spinner("Screener läuft. Earnings-Kalender und Kursdaten werden geladen..."):
        df = run_screen()
else:
    df = pd.read_csv(data_file)

if df.empty:
    st.warning("Keine Treffer für die aktuellen Filter.")
    st.stop()

col1, col2, col3, col4 = st.columns(4)

col1.metric("Treffer", len(df))
col2.metric("Top Momentum", f"{df['performance_2m_pct'].max():.1f} %")
col3.metric("A-Setups", len(df[df["rating"] == "A"]))
col4.metric("B-Setups", len(df[df["rating"] == "B"]))

st.divider()

rating_filter = st.multiselect(
    "Rating filtern",
    options=sorted(df["rating"].unique()),
    default=sorted(df["rating"].unique()),
)

filtered = df[df["rating"].isin(rating_filter)]

st.subheader("Screening-Ergebnisse")

st.dataframe(
    filtered,
    use_container_width=True,
    hide_index=True,
)

st.subheader("Top 10 nach 2-Monats-Momentum")

top10 = filtered.sort_values("performance_2m_pct", ascending=False).head(10)

st.bar_chart(
    top10,
    x="symbol",
    y="performance_2m_pct",
)

st.divider()

st.caption(
    "Hinweis: Dieses Tool ist ein technischer Screener, keine Anlageberatung. "
    "Starke Vorab-Performance vor Quartalszahlen kann auch bedeuten, dass hohe Erwartungen bereits eingepreist sind."
)
