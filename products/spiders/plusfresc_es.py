import json
import scrapy
from products.items import Product
from products.user_agents import FIREFOX_LATEST

class PlusfrescESSpider(scrapy.Spider):
    """
    Spider for Plusfresc (Spain).
    Uses the JSON API to fetch the category tree and crawl products.
    """
    name = "plusfresc_es"
    allowed_domains = ["plusfresc.cat", "wscompra.plusfresc.cat"]

    # We use CenterId = 12 (standard center ID used by their web app when not logged in)
    center_id = 12
    start_urls = [
        f"https://wscompra.plusfresc.cat/api/categories/tree/{center_id}/Root"
    ]

    custom_settings = {
        "USER_AGENT": FIREFOX_LATEST,
        "ROBOTSTXT_OBEY": False,
    }

    def parse(self, response):
        try:
            data = json.loads(response.text)
        except Exception as e:
            self.logger.error(f"Failed to parse JSON from {response.url}: {e}")
            return

        category_root = data.get("category", {})
        yield from self.parse_categories(category_root)

    def parse_categories(self, category):
        childs = category.get("childs", [])
        cat_id = category.get("id")

        if childs:
            for child in childs:
                yield from self.parse_categories(child)
        elif cat_id:
            # Skip promotional or non-numeric categories if they are not product lists
            # The standard product categories have numeric IDs (e.g., '080201' or similar)
            if cat_id.isdigit():
                products_url = f"https://wscompra.plusfresc.cat/api/products/category/{cat_id}/{self.center_id}"
                yield scrapy.Request(
                    url=products_url,
                    callback=self.parse_products,
                    meta={"category_id": cat_id}
                )

    def parse_products(self, response):
        try:
            products_list = json.loads(response.text)
        except Exception as e:
            self.logger.error(f"Failed to parse products JSON from {response.url}: {e}")
            return

        category_id = response.meta.get("category_id")

        for p in products_list:
            # Skip unavailable items if desired, but we can capture them anyway or filter them.
            # Usually we capture them but we should make sure pricing is present.
            if not p.get("available"):
                continue

            product = Product()

            item_id = p.get("item_id") or p.get("id")
            if not item_id:
                continue

            product["ref"] = item_id

            # Prefer es (Spanish) or ca (Catalan) for names
            texts = p.get("texts", [])
            name = None
            # Try to find Catalan text first, or Spanish, or any text
            for lang_pref in ["ca", "es"]:
                for t in texts:
                    if t.get("lang") == lang_pref and t.get("type") == 4 and t.get("text"):
                        name = t.get("text").strip()
                        break
                if name:
                    break

            if not name:
                for t in texts:
                    if t.get("type") == 4 and t.get("text"):
                        name = t.get("text").strip()
                        break

            if not name:
                # Fallback to any first text
                for t in texts:
                    if t.get("text"):
                        name = t.get("text").strip()
                        break

            if not name:
                continue

            product["name"] = name

            # Brand name
            brand = p.get("brand_name")
            if brand:
                product["brand"] = brand.strip()

            # Price extraction (new_value_cents takes priority as promo price, else value_cents)
            price_cents = p.get("new_value_cents") or p.get("value_cents")
            if price_cents is not None:
                product["price"] = f"{price_cents / 100:.2f}"
                product["proof_currency"] = "EUR"

            # Image
            image_url = p.get("image_url") or p.get("icon")
            if image_url:
                # Base image URL as defined in their config
                product["image"] = f"https://compra.plusfresc.cat/ImatgesProductes/{image_url}"

            # Website PDP URL structure
            product["website"] = f"https://compra.plusfresc.cat/product-detail/{item_id}"

            # Wikidata info
            product["located_in_wikidata"] = "Q111373081"

            yield product
