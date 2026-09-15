"""
Wazobia Market price comparison — Step 5: interactive dashboard
Run with: streamlit run dashboard.py

Uses MEDIAN instead of AVERAGE for the same reason as analysis_sql.py —
resistant to one outlier row skewing the whole category's comparison.
"""

from pathlib import Path
import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "prices.db"

ORANGE = "#E8630A"
BLACK = "#0A0A0A"

st.set_page_config(page_title="Wazobia Market Price Comparison", layout="wide")

if not DB_PATH.exists():
    st.error(
        f"Database file not found at: `{DB_PATH}`. "
        "Please run `build_db.py` first to generate the SQLite database."
    )
    st.stop()

conn = sqlite3.connect(DB_PATH)
df = pd.read_sql_query("SELECT * FROM prices", conn)
conn.close()

# Scale the raw unit price (per 1g/ml) to a user-friendly metric (per 100g/ml)
df["unit_price_100g"] = df["unit_price"] * 100

st.title("Is Wazobia Market actually pricier than competitors?")
st.caption("Actually with Marvellous — real price data, normalized per 100g / 100ml, median-based")

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

comparable_df = filtered[filtered["canonical_item"].isin(comparable_items)]

if not comparable_df.empty:
    # MEDIAN instead of mean, plus item_count so thin categories are visible
    median_unit_price = comparable_df.groupby(["canonical_item", "business"])["unit_price_100g"].agg(
        unit_price_100g="median", item_count="count"
    ).reset_index()

    pivot = median_unit_price.pivot(index="canonical_item", columns="business", values="unit_price_100g")

    if "My Sasun" in pivot.columns and "Wazobia Market" in pivot.columns:
        pivot["pct_difference"] = ((pivot["Wazobia Market"] - pivot["My Sasun"]) / pivot["My Sasun"] * 100).round(1)
        median_diff = pivot["pct_difference"].median()
        cheaper_count = (pivot["pct_difference"] < 0).sum()
        total_count = len(pivot)

        st.subheader("Market Summary")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                label="Median Price Difference",
                value=f"{median_diff:+.1f}%",
                delta="Wazobia is Cheaper" if median_diff < 0 else "Wazobia is Pricier",
                delta_color="normal" if median_diff > 0 else "inverse"
            )
        with col2:
            st.metric(
                label="Wazobia Wins",
                value=f"{cheaper_count} / {total_count} items",
                delta=f"{(cheaper_count / total_count * 100):.1f}% of items cheaper"
            )
        with col3:
            st.metric(label="Total Overlapping Items", value=total_count)
        st.divider()

st.subheader(f"Unit price comparison — items sold by both stores ({len(comparable_items)} items)")

if comparable_df.empty:
    st.warning("No items overlap between the selected businesses yet. "
               "Fill in more rows in wazobia_manual_prices.csv to get more overlap.")
else:
    fig = px.bar(
        median_unit_price, x="canonical_item", y="unit_price_100g", color="business",
        barmode="group", color_discrete_map={"My Sasun": BLACK, "Wazobia Market": ORANGE},
        labels={"unit_price_100g": "Median price per 100g / 100ml ($)", "canonical_item": "Item"}
    )
    st.plotly_chart(fig, use_container_width=True)

    if "My Sasun" in pivot.columns and "Wazobia Market" in pivot.columns:
        clean_pivot = pivot.reset_index()
        clean_pivot.columns.name = None
        clean_pivot = clean_pivot.rename(columns={
            "canonical_item": "Product Item",
            "pct_difference": "% Price Difference"
        })

        st.subheader("% price difference (Wazobia vs. My Sasun, median-based)")
        st.caption("Negative values mean Wazobia is cheaper. Check item_count in the raw "
                   "data below — a category backed by only 1-2 rows is a thinner claim "
                   "than one backed by several.")

        st.dataframe(
            clean_pivot.sort_values("% Price Difference", ascending=False),
            use_container_width=True,
            column_config={
                "My Sasun": st.column_config.NumberColumn("My Sasun (Per 100g/ml)", format="$%.2f"),
                "Wazobia Market": st.column_config.NumberColumn("Wazobia (Per 100g/ml)", format="$%.2f"),
                "% Price Difference": st.column_config.NumberColumn("% Difference", format="%+0.1f%%")
            }
        )

with st.expander("See all normalized data (including items only one store sells)"):
    st.dataframe(filtered, use_container_width=True)
