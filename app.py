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
            "exchange": "Börse",
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
            "data_source": "Datenquelle",
        }
    )


def show_table(df):
    st.dataframe(
        df,
        width="stretch",
        hide_index=True,
       
