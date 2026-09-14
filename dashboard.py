"""
Wazobia Market price comparison — Step 5 (was Step 4): interactive dashboard
Run with: streamlit run dashboard.py
"""

from pathlib import Path
import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as st

# Get the directory where this script is located
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "prices.db"

ORANGE = "#E8630A"
BLACK = "#0A0A0A"

st.set_page_config(page_title="Wazobia Market Price Comparison", layout="wide")

# Ensure the database exists before attempting to connect
if not DB_PATH.exists():
    st.error(
        f"Database file not found at: `{DB_PATH}`. "
        "Please run `build_db.py` first to generate the SQLite database."
    )
    st.stop()

conn = sqlite3.connect(DB_PATH)
df = pd.read_sql_query("SELECT * FROM prices", conn)
conn.close()

st.title("Is Wazobia Market actually pricier than competitors?")
st.caption("Actually with Marvellous — real price data, normalized per unit weight")

st.sidebar.header("Filters")
items = st.sidebar.multiselect(
    "Item", options=sorted(df["canonical_item"].unique()),
    default=sorted(df["canonical_item"].unique())
)
businesses = st.sidebar.multiselect(
    "Business", options=sorted(df["business"].unique()),
    default=sorted(df["business"].unique())
)

filtered = df[df["canonical_item"].isin(items) & df["business"].isin(businesses)]

# Only items both stores sell — this is the real comparison
both_stores = filtered.groupby("canonical_item")["business"].nunique()
comparable_items = both_stores[both_stores == df["business"].nunique()].index.tolist()

st.subheader(f"Unit price comparison — items sold by both stores ({len(comparable_items)} items)")
comparable_df = filtered[filtered["canonical_item"].isin(comparable_items)]

if comparable_df.empty:
    st.warning("No items overlap between the selected businesses yet. "
               "Fill in more rows in wazobia_manual_prices.csv to get more overlap.")
else:
    avg_unit_price = comparable_df.groupby(["canonical_item", "business"])["unit_price"].mean().reset_index()
    fig = px.bar(
        avg_unit_price, x="canonical_item", y="unit_price", color="business",
        barmode="group", color_discrete_map={"My Sasun": BLACK, "Wazobia Market": ORANGE},
        labels={"unit_price": "Price per gram/ml ($)"}
    )
    st.plotly_chart(fig, use_container_width=True)

    # % difference table
    pivot = avg_unit_price.pivot(index="canonical_item", columns="business", values="unit_price")
    if "My Sasun" in pivot.columns and "Wazobia Market" in pivot.columns:
        pivot["pct_difference"] = ((pivot["Wazobia Market"] - pivot["My Sasun"]) / pivot["My Sasun"] * 100).round(1)
        st.subheader("% price difference (Wazobia vs. My Sasun)")
        st.dataframe(pivot.sort_values("pct_difference", ascending=False), use_container_width=True)

with st.expander("See all normalized data (including items only one store sells)"):
    st.dataframe(filtered, use_container_width=True)
