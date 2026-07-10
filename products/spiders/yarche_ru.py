import re
import chompjs
from products.items import Product
from scrapy.http import Response
from scrapy.spiders import SitemapSpider
from products.structured_data_spider import StructuredDataSpider

class YarcheRUSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Ярче! (Yarche) (Russia).
    Wikidata: Q102254456
    """

    name = "yarche_ru"
    allowed_domains = ["yarcheplus.ru"]
    sitemap_urls = ["https://yarcheplus.ru/sitemap-product-offer.xml"]
    sitemap_rules = [(r"/product/", "parse_sd")]

    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
    }

    item_attributes = {
        "located_in_wikidata": "Q102254456",
    }

    def post_process_item(self, item: Product, response: Response, ld_data: dict, **kwargs):
        for key, value in self.item_attributes.items():
            item[key] = value
        yield item

    def iter_linked_data(self, response: Response):
        # Extract product ID from URL
        url_match = re.search(r"-(\d+)$", response.url)
        if not url_match:
            return

        product_id = url_match.group(1)
        # Find the product JSON object in the page content
        # It's usually embedded in a large state object.
        # We find the start and then balance the braces.
        start_pattern = r'\{"id":' + product_id + r','
        match = re.search(start_pattern, response.text)

        if match:
            try:
                start_index = match.start()
                count = 0
                end_index = -1
                for i in range(start_index, len(response.text)):
                    if response.text[i] == "{":
                        count += 1
                    elif response.text[i] == "}":
                        count -= 1
                        if count == 0:
                            end_index = i + 1
                            break

                if end_index == -1:
                    return

                obj_str = response.text[start_index:end_index]
                product = chompjs.parse_js_object(obj_str)
                if product:
                    image_id = product.get("image", {}).get("id")
                    image_url = None
                    if image_id:
                        id_str = str(image_id)
                        # Path pattern: first 2 digits / next 3 digits (or less) / full id
                        # Example: 55519 -> 55 / 519 / 55519
                        # Example: 9000 -> 90 / 00 / 9000
                        if len(id_str) >= 2:
                            path = f"{id_str[:2]}/{id_str[2:]}/{id_str}"
                            image_url = f"https://api.yarcheplus.ru/thumbnail/768x768/{path}.png"

                    price = product.get("price")
                    currency = product.get("quant", {}).get("currency")
                    if not currency and (price is not None and price > 0):
                        currency = "RUB"

                    yield {
                        "@type": "Product",
                        "name": product.get("name"),
                        "description": product.get("description"),
                        "brand": {"@type": "Brand", "name": product.get("brand")}
                        if product.get("brand")
                        else None,
                        "sku": str(product.get("id")),
                        "image": image_url,
                        "offers": [
                            {
                                "@type": "Offer",
                                "price": price,
                                "priceCurrency": currency,
                                "availability": "https://schema.org/InStock"
                                if product.get("isAvailable")
                                else "https://schema.org/OutOfStock",
                            }
                        ],
                    }
            except Exception:
                self.logger.debug("Failed to parse product object for ID %s", product_id)
