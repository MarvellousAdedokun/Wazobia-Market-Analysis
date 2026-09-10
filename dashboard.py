"""
Wazobia Market price comparison — Step 4: interactive dashboard
Run with: streamlit run dashboard.py
"""

import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

DB_PATH = "prices.db"

# ForgeLabs brand colors
ORANGE = "#E8630A"
BLACK = "#0A0A0A"

st.set_page_config(page_title="Wazobia Market Price Comparison", layout="wide")

conn = sqlite3.connect(DB_PATH)
df = pd.read_sql_query("SELECT * FROM prices", conn)
conn.close()

st.title("Is Wazobia Market actually pricier than competitors?")
st.caption("Actually with Marvellous — real price data, no guessing")

# Sidebar filters
st.sidebar.header("Filters")
categories = st.sidebar.multiselect(
    "Category", options=sorted(df["category"].dropna().unique()),
    default=sorted(df["category"].dropna().unique())
)
businesses = st.sidebar.multiselect(
    "Business", options=sorted(df["business"].unique()),
    default=sorted(df["business"].unique())
)

filtered = df[df["category"].isin(categories) & df["business"].isin(businesses)]

# Top-level metric
col1, col2 = st.columns(2)
with col1:
    avg_by_business = filtered.groupby("business")["price"].mean().round(2)
    for biz, avg in avg_by_business.items():
        st.metric(f"{biz} — avg price", f"${avg}")

# Category comparison chart
st.subheader("Average price by category")
category_avg = filtered.groupby(["category", "business"])["price"].mean().reset_index()
fig = px.bar(
    category_avg, x="category", y="price", color="business",
    barmode="group", color_discrete_map={"My Sasun": BLACK, "Wazobia Market": ORANGE}
)
st.plotly_chart(fig, use_container_width=True)

# Head-to-head table for products both sell
st.subheader("Head-to-head: same product, different store")
mysasun = filtered[filtered["business"] == "My Sasun"][["product_name", "price"]]
wazobia = filtered[filtered["business"] == "Wazobia Market"][["product_name", "price"]]
merged = mysasun.merge(wazobia, on="product_name", suffixes=("_mysasun", "_wazobia"))
merged["difference"] = (merged["price_wazobia"] - merged["price_mysasun"]).round(2)
st.dataframe(merged, use_container_width=True)

# Raw data, for transparency
with st.expander("See raw data"):
    st.dataframe(filtered, use_container_width=True)
