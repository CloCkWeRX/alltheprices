import base64
import json
import re
import scrapy
from urllib.parse import unquote
from products.items import Product
from products.user_agents import FIREFOX_LATEST

class ShoppersfoodUSSpider(scrapy.Spider):
    """
    Shoppers Food & Pharmacy (United States) spider.
    Wikidata: Q7501183

    This spider uses the Swiftly API to fetch product data with prices.
    It first visits the categories page to obtain a session token from the __session cookie.
    """
    name = "shoppersfood_us"
    allowed_domains = ["shoppersfood.com", "swiftlyapi.net"]

    # Store ID 2279 is MLK in Landover, MD
    store_id = "2279"
    api_base_url = "https://prod.swiftlyapi.net/search/api/v1/products/categories"

    custom_settings = {
        "USER_AGENT": FIREFOX_LATEST,
        "ROBOTSTXT_OBEY": False,
        "CONCURRENT_REQUESTS": 2,
    }

    def start_requests(self):
        # Initial request to get the __session cookie
        yield scrapy.Request(
            "https://www.shoppersfood.com/categories",
            callback=self.parse_session
        )

    def parse_session(self, response):
        session_cookies = response.headers.getlist('Set-Cookie')
        token = None
        for cookie_bytes in session_cookies:
            cookie_str = cookie_bytes.decode('utf-8')
            if '__session=' in cookie_str:
                match = re.search(r'__session=([^;]*)', cookie_str)
                if match:
                    encoded_session = unquote(match.group(1))
                    try:
                        # The cookie is base64 encoded JSON followed by a signature (sometimes multiple parts)
                        # We only need the first part which is the JSON payload
                        payload = encoded_session.split('.')[0]
                        payload += '=' * (4 - len(payload) % 4)
                        session_data = json.loads(base64.b64decode(payload))
                        token = session_data.get('token')
                        if token:
                            break
                    except Exception:
                        continue

        if not token:
            self.logger.error("Could not extract token from __session cookie")
            return

        # List of top level categories
        categories = [
            "Product/alcoholic-beverages", "Product/bakery", "Product/beverages",
            "Product/breakfast-and-cereal", "Product/condiments-and-dressings",
            "Product/cooking-and-baking", "Product/dairy", "Product/deli",
            "Product/floral-and-garden", "Product/frozen", "Product/health-and-beauty",
            "Product/household-cleaning-and-paper", "Product/household-supplies",
            "Product/international-foods", "Product/meat-and-seafood",
            "Product/office-and-party-supplies", "Product/pet", "Product/produce",
            "Product/seasonal-and-toys", "Product/sides-pastas-and-grains",
            "Product/snacks", "Product/soups-and-canned-goods", "Product/specialty-foods"
        ]

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Origin": "https://www.shoppersfood.com",
            "Referer": "https://www.shoppersfood.com/",
        }

        for cat in categories:
            url = f"{self.api_base_url}?cat={cat.replace('/', '%2F')}&store={self.store_id}&limit=100&offset=0"
            yield scrapy.Request(
                url,
                headers=headers,
                callback=self.parse_api,
                meta={'token': token, 'cat': cat, 'offset': 0, 'headers': headers}
            )

    def parse_api(self, response):
        data = response.json()
        # In the Swiftly API, products are under products -> items
        products_info = data.get('products', {})
        products = products_info.get('items', [])

        for p_data in products:
            product = Product()
            product["name"] = p_data.get("name")
            product["ref"] = p_data.get("id")
            # Build website URL
            product["website"] = f"https://www.shoppersfood.com/categories/{response.meta['cat'].replace('/', '%2F')}/product/{p_data.get('id')}"
            product["description"] = p_data.get("description")
            product["brand"] = p_data.get("brand")

            if primary_image := p_data.get("primaryImage"):
                product["image"] = primary_image.get("url")

            price_info = p_data.get("price", {}).get("ok", {})
            if price_info:
                reg_text = price_info.get("regPriceText", "")
                promo_text = price_info.get("promoArea", {}).get("promoText", "")

                # Simple extraction of price from text (e.g. "$3.99" or "$5")
                price_match = re.search(r'\$(\d+(?:\.\d{2})?)', promo_text or reg_text)
                if price_match:
                    product["price"] = price_match.group(1)
                    product["proof_currency"] = "USD"

                if promo_text:
                    product["price_is_discounted"] = True
                    reg_match = re.search(r'\$(\d+(?:\.\d{2})?)', reg_text)
                    if reg_match:
                        product["price_without_discount"] = reg_match.group(1)

            # GTIN extraction from productCodes or attributes
            if codes := p_data.get("productCodes"):
                if isinstance(codes, list):
                    # Usually the first is the 14-digit GTIN or similar
                    for code in codes:
                        if len(code) >= 12:
                            product["gtin"] = code
                            break

            product["located_in_wikidata"] = "Q7501183"
            yield product

        # Pagination
        if len(products) == 100:
            new_offset = response.meta['offset'] + 100
            url = f"{self.api_base_url}?cat={response.meta['cat'].replace('/', '%2F')}&store={self.store_id}&limit=100&offset={new_offset}"
            yield scrapy.Request(
                url,
                headers=response.meta['headers'],
                callback=self.parse_api,
                meta={
                    'token': response.meta['token'],
                    'cat': response.meta['cat'],
                    'offset': new_offset,
                    'headers': response.meta['headers']
                }
            )
