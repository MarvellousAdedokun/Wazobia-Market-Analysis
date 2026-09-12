"""
Wazobia Market price comparison — normalization step
Converts every item to a price-per-unit-weight (or per-liter for oils),
and tags each row with a canonical_item so different pack sizes and
naming across stores can be fairly compared.

Run this AFTER scrape_mysasun.py and AFTER filling in wazobia_manual_prices.csv.
"""

import pandas as pd
import re

# --- Unit conversion: everything to grams (weight) or ml (volume) ---
WEIGHT_TO_GRAMS = {"lb": 453.592, "lbs": 453.592, "kg": 1000, "g": 1, "oz": 28.3495}
VOLUME_TO_ML = {"l": 1000, "ml": 1}

# --- Canonical categories: keyword -> canonical_item label ---
# Order matters — more specific keywords first, so "poundo yam" is checked
# before generic "yam flour" would wrongly match it.
CANONICAL_RULES = [
    ("locust bean", None),       # Iru/dawadawa — a seasoning, not a staple we're comparing
    ("iru", None),
    ("poundo yam", "Poundo Yam Flour"),
    ("yam flour", "Yam Flour (Elubo)"),
    ("elubo", "Yam Flour (Elubo)"),
    ("rice flour", "Rice Flour"),      # different product from whole rice — keep separate
    ("beans flour", "Beans Flour"),    # different product from whole beans — keep separate
    ("garri", "Garri"),
    ("gari", "Garri"),
    ("palm oil", "Palm Oil"),
    ("egusi", "Egusi"),
    ("ogbono", "Ogbono"),
    ("crayfish", "Crayfish"),
    ("stockfish", "Stockfish"),
    ("plantain chips", "Plantain Chips"),
    ("bitter leaf", "Bitter Leaf"),
    ("beans", "Beans"),
    ("rice", "Rice"),
    ("indomie", "Indomie Noodles"),
    ("milo", "Milo"),
    ("peak milk", "Peak Evaporated Milk"),
]


def assign_canonical_item(product_name):
    name_lower = product_name.lower()
    for keyword, canonical in CANONICAL_RULES:
        if keyword in name_lower:
            return canonical  # may be None on purpose — excludes non-staple matches
    return None


def extract_size(text):
    """
    Pulls a (quantity, unit) pair out of messy text like:
    '5lbs', '10L', '400g', '2.5oz', '25lbs'
    Returns (quantity_in_base_unit, unit_type) where unit_type is
    'weight' (grams) or 'volume' (ml). Returns (None, None) if no match.
    """
    text = text.lower()
    # Keep real spaces in the text (don't strip them) so the word-boundary
    # check after the unit works correctly even when more text follows,
    # e.g. "10L Default Title" — stripping spaces here previously broke this.
    weight_match = re.search(r"(\d+\.?\d*)\s*(lbs|lb|kg|g|oz)\b", text)
    if weight_match:
        qty, unit = weight_match.groups()
        return float(qty) * WEIGHT_TO_GRAMS[unit], "weight"

    volume_match = re.search(r"(\d+\.?\d*)\s*(ml|l)\b", text)
    if volume_match:
        qty, unit = volume_match.groups()
        return float(qty) * VOLUME_TO_ML[unit], "volume"

    return None, None


def normalize_dataframe(df):
    """
    Adds canonical_item, size_grams_or_ml, unit_type, and unit_price columns.
    Drops rows that don't match a known staple category or have no parseable size.
    """
    df = df.copy()
    df["canonical_item"] = df["product_name"].apply(assign_canonical_item)

    # Combine product_name + variant text, since size sometimes lives in
    # the variant field (e.g. product_name="Sasun Garri Ijebu | Gari", variant="5lbs")
    combined_text = df["product_name"].fillna("") + " " + df["variant"].fillna("")
    sizes = combined_text.apply(extract_size)
    df["size_base_unit"] = sizes.apply(lambda x: x[0])
    df["unit_type"] = sizes.apply(lambda x: x[1])

    # Drop rows with no canonical category, no parseable size, or zero price
    df = df.dropna(subset=["canonical_item", "size_base_unit"])
    df = df[df["price"] > 0]

    df["unit_price"] = (df["price"] / df["size_base_unit"]).round(4)
    return df


def normalize_dataframe(df, size_col="variant"):
    """
    Adds canonical_item, size_base_unit, unit_type, and unit_price columns.
    Drops rows that don't match a known staple category or have no parseable size.

    size_col: name of the column holding size/variant text (e.g. "variant" for
    the My Sasun scrape, "size" for the manually-entered Wazobia data).
    """
    df = df.copy()
    df["canonical_item"] = df["product_name"].apply(assign_canonical_item)

    combined_text = df["product_name"].fillna("") + " " + df[size_col].fillna("")
    sizes = combined_text.apply(extract_size)
    df["size_base_unit"] = sizes.apply(lambda x: x[0])
    df["unit_type"] = sizes.apply(lambda x: x[1])

    df = df.dropna(subset=["canonical_item", "size_base_unit"])
    df = df[df["price"] > 0]

    df["unit_price"] = (df["price"] / df["size_base_unit"]).round(4)
    return df


if __name__ == "__main__":
    # --- My Sasun (scraped) ---
    mysasun_df = pd.read_csv("mysasun_prices.csv")
    mysasun_norm = normalize_dataframe(mysasun_df, size_col="variant")
    print(f"My Sasun: normalized {len(mysasun_norm)} of {len(mysasun_df)} rows")

    # --- Wazobia (manually entered) ---
    wazobia_df = pd.read_csv("wazobia_manual_prices.csv")
    wazobia_df = wazobia_df.dropna(subset=["price"])  # skip rows not filled in yet
    wazobia_norm = normalize_dataframe(wazobia_df, size_col="size")
    print(f"Wazobia: normalized {len(wazobia_norm)} of {len(wazobia_df)} filled-in rows")

    combined = pd.concat([mysasun_norm, wazobia_norm], ignore_index=True)
    combined.to_csv("combined_normalized.csv", index=False)
    print(f"\nSaved {len(combined)} total rows to combined_normalized.csv")
    print("\nCanonical items found in both stores (these are the ones you can actually compare):")
    both = combined.groupby("canonical_item")["business"].nunique()
    print(both[both == 2].index.tolist())

