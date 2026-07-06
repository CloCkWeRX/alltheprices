import re
import chompjs
from scrapy.http import Response
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from products.items import Product
from products.structured_data_spider import StructuredDataSpider

class KirmarketRUSpider(CrawlSpider, StructuredDataSpider):
    """
    Spider for Kirovsky (Russia).
    Wikidata: Q4221634

    Sample output:
    {
        "name": "Масло Сыробогатов Крестьянское 72,5% 175г",
        "website": "https://kirmarket.ru/catalog/detail.php?ELEMENT_ID=92917",
        "image": "https://kirmarket.ru/upload/iblock/d07/omyulrok3rxw2us2t1lonus4qivkkrwl.webp",
        "ref": "92917",
        "located_in_wikidata": "Q4221634",
        "offers": [
            {
                "@type": "Offer",
                "price": "149.99",
                "priceCurrency": "RUB",
                "availability": "https://schema.org/InStock"
            }
        ]
    }
    """

    name = "kirmarket_ru"
    allowed_domains = ["kirmarket.ru"]
    start_urls = ["https://kirmarket.ru/catalog/"]

    rules = (
        # Follow categories
        Rule(LinkExtractor(allow=r"/catalog/[A-Z0-9_-]+/$")),
        # Parse products
        Rule(LinkExtractor(allow=(r"ELEMENT_ID=(\d+)", r"/catalog/product/([^/]+)/")), callback="parse_sd"),
    )

    item_attributes = {
        "located_in_wikidata": "Q4221634",
    }

    def iter_linked_data(self, response: Response):
        # Extract from JSCatalogElement JS block
        # Start matching from the opening brace and let chompjs handle the end of the object
        pattern = r"new JSCatalogElement\((\{.*)"
        match = re.search(pattern, response.text, re.DOTALL)
        if match:
            try:
                data = chompjs.parse_js_object(match.group(1))
                product_data = data.get("PRODUCT", {})
                name = product_data.get("NAME")
                ref = product_data.get("ID")

                pict = product_data.get("PICT", {})
                image = pict.get("SRC")
                if image and not image.startswith("http"):
                    image = response.urljoin(image)

                prices = product_data.get("ITEM_PRICES", [])
                price = None
                currency = "RUB"
                if prices:
                    # Clean price from non-breaking spaces
                    price_raw = str(prices[0].get("PRICE", ""))
                    price = price_raw.replace("\u00a0", "").replace(" ", "")
                    currency = prices[0].get("CURRENCY", "RUB")

                if name:
                    yield {
                        "@type": "Product",
                        "name": name,
                        "image": image,
                        "sku": ref,
                        "offers": [{
                            "@type": "Offer",
                            "price": price,
                            "priceCurrency": currency,
                            "availability": "https://schema.org/InStock" if product_data.get("CAN_BUY") else "https://schema.org/OutOfStock",
                        }],
                    }
                    return
            except Exception:
                self.logger.debug("Failed to parse JSCatalogElement", exc_info=True)

        # Fallback for pages without JSCatalogElement
        name = response.css(".pref__title.main-titles::text").get()
        if not name:
            name = response.css("h1::text").get()

        if name:
            name = name.strip()
            image = response.css(".detail__pic img::attr(src)").get()
            if image and not image.startswith("http"):
                image = response.urljoin(image)

            price_raw = response.css(".catalog-card__new-price::text").get()
            price = price_raw.replace("\u00a0", "").replace(" ", "") if price_raw else None

            yield {
                "@type": "Product",
                "name": name,
                "image": image,
                "offers": [{
                    "@type": "Offer",
                    "price": price,
                    "priceCurrency": "RUB",
                    "availability": "https://schema.org/InStock" if "В наличии" in response.text else "https://schema.org/OutOfStock",
                }],
            }

    def post_process_item(self, item: Product, response: Response, ld_data: dict, **kwargs):
        # Prefer numeric ID from HTML if available (from detail container)
        match = re.search(r'class="[^"]*catalog__detail[^"]*"[^>]*id="bx_\d+_(\d+)"', response.text)
        if match:
            item["ref"] = match.group(1)
        elif not item.get("ref") or item["ref"].startswith("http"):
            if ld_data.get("sku"):
                item["ref"] = ld_data["sku"]
            else:
                # Use slug from URL
                parts = response.url.strip("/").split("/")
                if parts:
                    item["ref"] = parts[-1]

        yield item
