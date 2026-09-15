"""
Wazobia Market price comparison — Step 4: SQL analysis
Compares UNIT PRICE (price per gram/ml) across canonical items, not raw price
— this is what makes the comparison fair across different pack sizes.

Uses MEDIAN instead of AVERAGE — a plain average gets dragged around by one
outlier row (a mistyped price, a genuinely weird deal); median resists that,
since it only cares about the middle value, not how extreme the extremes are.
SQLite has no built-in MEDIAN(), so we pull raw rows and compute it in pandas.
"""

from pathlib import Path
import sqlite3
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "prices.db"


def get_raw_prices():
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database file not found at: {DB_PATH}\n"
            f"Please run 'build_db.py' first to initialize the database."
        )
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT canonical_item, business, unit_price FROM prices", conn)
    conn.close()
    return df


def median_by_category(df):
    """Median unit price per business, per canonical item — plus how many
    rows back each median, so you can see which numbers are thin (1-2 rows)
    versus well-supported (several rows)."""
    result = df.groupby(["canonical_item", "business"])["unit_price"].agg(
        median_unit_price="median", item_count="count"
    ).reset_index()
    return result.sort_values(["canonical_item", "business"])


def head_to_head(df):
    """Only items both stores sell, comparing median unit price, with %
    difference. This is the number that actually goes in the episode."""
    my_sasun = df[df["business"] == "My Sasun"].groupby("canonical_item")["unit_price"].median()
    wazobia = df[df["business"] == "Wazobia Market"].groupby("canonical_item")["unit_price"].median()

    combined = pd.concat(
        [my_sasun.rename("mysasun_median"), wazobia.rename("wazobia_median")], axis=1
    ).dropna()  # only keep items present in both

    combined["pct_difference"] = (
        (combined["wazobia_median"] - combined["mysasun_median"]) / combined["mysasun_median"] * 100
    ).round(1)

    return combined.round(5).sort_values("pct_difference", ascending=False)


if __name__ == "__main__":
    raw = get_raw_prices()

    print("=== Median unit price by canonical item and business ===")
    print(median_by_category(raw).to_string())

    print("\n=== Head-to-head: items both stores sell (% difference, median-based) ===")
    result = head_to_head(raw)
    if result.empty:
        print("No overlapping canonical items yet — check that Wazobia's product_name "
              "text contains one of the same category keywords (garri, palm oil, "
              "egusi, etc.) as normalize.py looks for.")
    else:
        print(result.to_string())
