"""
Wazobia Market price comparison — Step 1: pull My Sasun product data
My Sasun runs on Shopify, which exposes a free public JSON endpoint:
https://{store}/products.json — no auth, no scraping tricks needed.
"""

import requests
import pandas as pd
import time

BASE_URL = "https://mysasun.com/products.json"

# Staple items we care about for comparison — matched against Wazobia manually.
# Keep this list broad; we filter down after pulling.
TARGET_KEYWORDS = [
    "garri", "gari", "egusi", "palm oil", "poundo", "yam flour", "elubo",
    "crayfish", "stockfish", "ogbono", "plantain chips", "bitter leaf",
    "beans", "rice", "suya", "indomie", "milo", "peak milk"
]


def pull_all_products():
    """Shopify paginates 30 products per page by default via ?page= param."""
    all_products = []
    page = 1
    while True:
        resp = requests.get(BASE_URL, params={"page": page, "limit": 250})
        data = resp.json()
        products = data.get("products", [])
        if not products:
            break
        all_products.extend(products)
        page += 1
        time.sleep(0.5)  # polite delay, don't hammer their server
    return all_products


def flatten_products(products):
    """Each Shopify product can have multiple variants (sizes) with different prices."""
    rows = []
    for p in products:
        title = p.get("title", "")
        product_type = p.get("product_type", "")
        for variant in p.get("variants", []):
            rows.append({
                "business": "My Sasun",
                "product_name": title,
                "variant": variant.get("title", ""),
                "category": product_type,
                "price": float(variant.get("price", 0)),
            })
    return pd.DataFrame(rows)


def filter_to_staples(df):
    """Keep only rows matching our target staple keywords."""
    pattern = "|".join(TARGET_KEYWORDS)
    mask = df["product_name"].str.lower().str.contains(pattern, na=False)
    return df[mask].reset_index(drop=True)


if __name__ == "__main__":
    print("Pulling all My Sasun products...")
    raw_products = pull_all_products()
    print(f"Pulled {len(raw_products)} total products")

    df = flatten_products(raw_products)
    print(f"Flattened to {len(df)} product variants")

    staples_df = filter_to_staples(df)
    print(f"Filtered to {len(staples_df)} staple-matching rows")
    print(staples_df.head(20))

    staples_df.to_csv("mysasun_prices.csv", index=False)
    print("Saved to mysasun_prices.csv")
