# Shopify Client Reference

This module (`shopify_client.py`) wraps a few helper calls around the Shopify Admin API so the Terrain chatbot can fetch book information from the connected store. The helpers rely on environment variables for credentials and return raw Shopify objects so downstream layers can decide how to present the data.

## Environment Setup

Add the following keys to your `.env` file before using the client:

- `SHOPIFY_SHOP_NAME` – the subdomain of the Shopify store (e.g. `terrain-library`).
- `SHOPIFY_ACCESS_TOKEN` – Admin API access token with read permissions for products.

The module automatically calls `dotenv.load_dotenv()` and raises a `ValueError` if either key is missing. API requests target the 2025-01 Admin API (`BASE_URL = https://<shop>.myshopify.com/admin/api/2025-01`).

## Session Behaviour

The client creates a shared `requests.Session` with the required `X-Shopify-Access-Token` header and JSON content type. All helper functions use this session so connections are pooled automatically. Requests time out after 15–30 seconds depending on the call.

## Helper Functions

### `check_connection() -> bool`

- Endpoint: `GET /shop.json`
- Purpose: quick health-check during setup. Returns `True` when the API responds with HTTP 200; otherwise logs/prints a failure message and returns `False`.

### `get_book_by_title(title: str) -> dict | None`

- Endpoint: `GET /products.json?title=<title>`
- Purpose: fetch the first product whose title matches the query string.
- Returns: the first product object from Shopify (dict). If no match, returns `None`.

### `get_inventory_by_title(title: str) -> int | None`

- Uses `get_book_by_title` internally.
- Purpose: aggregate inventory across all variants for the given product title.
- Returns: total quantity (sum of `variant["inventory_quantity"]`). If no product is found, returns `None`.

### `get_price_by_title(title: str) -> str | None`

- Uses `get_book_by_title` internally.
- Purpose: report the price of the first variant of the matching product.
- Returns: price string (e.g. "24.99"). Returns `None` when the product or variants are missing.

### `get_type_by_title(title: str) -> str | None`

- Uses `get_book_by_title` internally.
- Purpose: expose Shopify's `product_type` for categorisation.
- Returns: product type string or `None` if the product is missing.

### `get_description_by_title(title: str) -> str | None`

- Uses `get_book_by_title` internally.
- Purpose: convert Shopify's HTML description to plain text using BeautifulSoup.
- Returns: cleaned description string stripped of HTML entities; `None` if no product exists.

## Usage Tips

- The helper functions return raw Shopify payloads. Downstream callers should handle localization and user-facing phrasing.
- Shopify's Admin API performs partial matches on the `title` query. Be prepared for multiple products matching similar titles; this helper always returns the first record.
- Consider caching results or adding rate limits if you expect repeated queries during a single chat session.
