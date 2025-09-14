import os
import requests
from html import unescape
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from html import unescape
load_dotenv()

# Connect shopify API
SHOP_NAME = os.getenv("SHOPIFY_SHOP_NAME")
ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")

API_VERSION = "2025-01"
BASE_URL = f"https://{SHOP_NAME}.myshopify.com/admin/api/{API_VERSION}"

_session = requests.Session()
_session.headers.update({
    "X-Shopify-Access-Token": ACCESS_TOKEN,
    "Content-Type": "application/json",
})

# Check connection status
def check_connection() -> bool:
    url = f"{BASE_URL}/shop.json"
    try:
        resp = _session.get(url, timeout=15)
        if resp.status_code == 200:
            shop_name = resp.json().get("shop", {}).get("name")
            print(f"Connected to Shopify store")
            return True
        else:
            print(f"Connection failed. Status: {resp.status_code}.")
            return False
    except requests.RequestException as e:
        print(f"Connection error: {e}")
        return False


def get_book_by_title(title):
    url = f"{BASE_URL}/products.json?title={title}"
    resp = _session.get(url, timeout=30)
    resp.raise_for_status()
    products = resp.json().get("products", [])
    return products[0] if products else None

def get_inventory_by_title(title):
    p = get_book_by_title(title)
    if not p:
        return None
    variants = p.get("variants", [])
    total = sum((v.get("inventory_quantity") or 0) for v in variants)
    return total

def get_price_by_title(title):
    p = get_book_by_title(title)
    if not p:
        return None
    variants = p.get("variants", [])
    if not variants:
        return None
    return variants[0].get("price")

def get_type_by_title(title):
    p = get_book_by_title(title)
    return p.get("product_type") if p else None

def get_description_by_title(title):
    p = get_book_by_title(title)
    if not p:
        return None
    html = p.get("body_html") or ""
    soup = BeautifulSoup(unescape(html), "html.parser")
    return soup.get_text().strip()
