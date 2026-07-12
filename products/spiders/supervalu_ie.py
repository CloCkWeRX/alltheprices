import re
import chompjs
from scrapy.spiders import SitemapSpider
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST

class SupervaluIESpider(SitemapSpider, StructuredDataSpider):
    name = "supervalu_ie"
    allowed_domains = ["supervalu.ie"]

    item_attributes = {
        "located_in_wikidata": "Q7642081" # SuperValu Ireland
    }

    sitemap_urls = ["https://shop.supervalu.ie/sitemap.xml"]
    sitemap_rules = [
        (r'/product/.*-id-(\d+)$', "parse_sd"),
    ]

    custom_settings = {
        "USER_AGENT": FIREFOX_LATEST,
        "ROBOTSTXT_OBEY": False,
    }

    def iter_linked_data(self, response):
        # Extract from window.__PRELOADED_STATE__
        script_text = response.xpath('//script[contains(text(), "window.__PRELOADED_STATE__")]/text()').get()
        if script_text:
            match = re.search(r'window\.__PRELOADED_STATE__\s*=\s*(.*?);', script_text, re.DOTALL)
            if match:
                try:
                    state = chompjs.parse_js_object(match.group(1))
                    product_data = state.get("product")
                    if product_data and isinstance(product_data, dict) and product_data.get("sku"):
                        # Map to a pseudo LD-JSON Product object
                        ld_product = {
                            "@type": "Product",
                            "name": product_data.get("name"),
                            "sku": product_data.get("sku"),
                            "brand": product_data.get("brand"),
                            "description": product_data.get("description"),
                            "image": product_data.get("image", {}).get("default") if isinstance(product_data.get("image"), dict) else None,
                            "offers": {
                                "@type": "Offer",
                                "price": product_data.get("price"),
                                "priceCurrency": "EUR",
                                "availability": "https://schema.org/InStock" if product_data.get("available") else "https://schema.org/OutOfStock"
                            },
                            "price_without_discount": product_data.get("wasPrice"),
                            "is_discounted": product_data.get("isDiscounted")
                        }
                        yield ld_product
                except Exception as e:
                    self.logger.error(f"Error parsing __PRELOADED_STATE__: {e}")

        # Standard LD-JSON as fallback/supplement
        yield from super().iter_linked_data(response)

    def post_process_item(self, item, response, ld_data):
        item["proof_currency"] = "EUR"

        # Promotion from offers if not already set
        if not item.get("price") and item.get("offers"):
            offers = item["offers"]
            if isinstance(offers, list) and len(offers) > 0:
                item["price"] = offers[0].get("price")
            elif isinstance(offers, dict):
                item["price"] = offers.get("price")

        if item.get("price") and isinstance(item["price"], str):
            item["price"] = item["price"].replace("€", "").strip()

        # Handle discount info from our pseudo-LD data
        if "price_without_discount" in ld_data:
            pwd = ld_data["price_without_discount"]
            if pwd and isinstance(pwd, str):
                item["price_without_discount"] = pwd.replace("€", "").strip()
            elif pwd:
                item["price_without_discount"] = pwd

        if "is_discounted" in ld_data:
            item["price_is_discounted"] = ld_data["is_discounted"]

        yield item
