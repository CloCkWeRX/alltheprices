import base64
import json
import re
from urllib.parse import unquote
import scrapy
from products.items import Product
from products.user_agents import FIREFOX_LATEST


class LuckysupermarketsUSSpider(scrapy.Spider):
    """
    Lucky Supermarkets (United States) spider.
    Wikidata: Q6698114

    This spider uses the Swiftly API to fetch product data with prices.
    It first visits the home page to obtain a session token from the __session cookie.
    """

    name = "luckysupermarkets_us"
    allowed_domains = ["luckysupermarkets.com", "swiftlyapi.net"]

    # Store ID 212 has valid products/prices
    store_id = "212"
    api_base_url = "https://lu.swiftlyapi.net/search/api/v1/products/categories"

    custom_settings = {
        "USER_AGENT": FIREFOX_LATEST,
        "ROBOTSTXT_OBEY": False,
        "CONCURRENT_REQUESTS": 2,
    }

    def start_requests(self):
        # Initial request to get the __session cookie
        yield scrapy.Request(
            "https://luckysupermarkets.com/", callback=self.parse_session
        )

    def parse_session(self, response):
        session_cookies = response.headers.getlist("Set-Cookie")
        token = None
        for cookie_bytes in session_cookies:
            cookie_str = cookie_bytes.decode("utf-8")
            if "__session=" in cookie_str:
                match = re.search(r"__session=([^;]*)", cookie_str)
                if match:
                    encoded_session = unquote(match.group(1))
                    try:
                        # The cookie is base64 encoded JSON followed by a signature (sometimes multiple parts)
                        # We only need the first part which is the JSON payload
                        payload = encoded_session.split(".")[0]
                        payload += "=" * ((4 - len(payload) % 4) % 4)
                        session_data = json.loads(
                            base64.urlsafe_b64decode(payload).decode(
                                "utf-8", errors="ignore"
                            )
                        )
                        token = session_data.get("token")
                        if token:
                            break
                    except Exception:
                        continue

        if not token:
            self.logger.error("Could not extract token from __session cookie")
            return

        # List of top level categories
        categories = [
            "Product/baby_needs",
            "Product/beer_wine_spirits",
            "Product/beverage",
            "Product/bread_bakery",
            "Product/dairy_eggs_cheese",
            "Product/deli_counter",
            "Product/floral_garden",
            "Product/frozen_foods",
            "Product/health_beauty",
            "Product/household",
            "Product/meat_seafood",
            "Product/pantry",
            "Product/pet_care",
            "Product/produce",
            "Product/seasonal_merchandise",
            "Product/snacks",
        ]

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Origin": "https://luckysupermarkets.com",
            "Referer": "https://luckysupermarkets.com/",
            "x-swiftly-banner-id": "a3b11717-f4ca-4196-b670-e5142c205dee",
        }

        for cat in categories:
            url = f"{self.api_base_url}?cat={cat.replace('/', '%2F')}&store={self.store_id}&limit=100&offset=0"
            yield scrapy.Request(
                url,
                headers=headers,
                callback=self.parse_api,
                meta={
                    "token": token,
                    "cat": cat,
                    "offset": 0,
                    "headers": headers,
                },
            )

    def parse_price(self, price_str):
        if not price_str:
            return None
        # Check for dollar pattern: $3.99 or $5
        match_dollar = re.search(r"\$(\d+(?:\.\d{2})?)", price_str)
        if match_dollar:
            return float(match_dollar.group(1))
        # Check for cents pattern: 99¢ or 99c
        match_cents = re.search(r"(\d+)\s*[¢\u00a2c]", price_str)
        if match_cents:
            return float(match_cents.group(1)) / 100.0
        # Fallback to any numeric decimal sequence
        match_num = re.search(r"(\d+(?:\.\d{2})?)", price_str)
        if match_num:
            return float(match_num.group(1))
        return None

    def parse_api(self, response):
        try:
            data = response.json()
        except Exception:
            self.logger.error(
                f"Failed to parse JSON response from {response.url}"
            )
            return

        products_info = data.get("products", {})
        products = products_info.get("items", [])

        for p_data in products:
            product = Product()
            product["name"] = p_data.get("name")
            product["ref"] = p_data.get("id")
            # Build website URL
            product["website"] = (
                f"https://luckysupermarkets.com/categories/"
                f"{response.meta['cat'].replace('/', '%2F')}/product/{p_data.get('id')}"
            )
            product["description"] = p_data.get("description")
            product["brand"] = p_data.get("brand")

            if primary_image := p_data.get("primaryImage"):
                product["image"] = primary_image.get("url")

            price_info = p_data.get("price", {}).get("ok", {})
            if price_info:
                reg_text = price_info.get("regPriceText", "")
                promo_text = (
                    price_info.get("promoArea", {}).get("promoText", "")
                    if price_info.get("promoArea")
                    else ""
                )

                active_price_text = promo_text or reg_text
                price_val = self.parse_price(active_price_text)
                if price_val is not None:
                    product["price"] = price_val
                    product["proof_currency"] = "USD"

                if promo_text:
                    product["price_is_discounted"] = True
                    reg_val = self.parse_price(reg_text)
                    if reg_val is not None:
                        product["price_without_discount"] = reg_val

                # Extra check for price per unit e.g. /lb or /each
                combined_text = f"{reg_text} {promo_text}".lower()
                if "/lb" in combined_text or "per lb" in combined_text:
                    product["price_per"] = "lb"
                elif "/ea" in combined_text or "each" in combined_text:
                    product["price_per"] = "each"

            # GTIN extraction from productCodes
            if codes := p_data.get("productCodes"):
                if isinstance(codes, list):
                    # Usually the first is the 14-digit GTIN or similar
                    for code in codes:
                        if len(code) >= 12:
                            product["gtin"] = code
                            break

            product["located_in_wikidata"] = "Q6698114"
            yield product

        # Pagination
        if len(products) == 100:
            new_offset = response.meta["offset"] + 100
            url = (
                f"{self.api_base_url}?cat={response.meta['cat'].replace('/', '%2F')}"
                f"&store={self.store_id}&limit=100&offset={new_offset}"
            )
            yield scrapy.Request(
                url,
                headers=response.meta["headers"],
                callback=self.parse_api,
                meta={
                    "token": response.meta["token"],
                    "cat": response.meta["cat"],
                    "offset": new_offset,
                    "headers": response.meta["headers"],
                },
            )
