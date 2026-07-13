import json
from typing import Iterable

from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

from products.items import Product
from products.structured_data_spider import StructuredDataSpider


class HagkaupISSpider(CrawlSpider, StructuredDataSpider):
    """
    Hagkaup (Iceland) spider.
    Issue #227. Wikidata Q3482054.
    """

    name = "hagkaup_is"
    allowed_domains = ["hagkaup.is"]
    start_urls = ["https://www.hagkaup.is/"]

    rules = (
        # Categories
        Rule(LinkExtractor(allow=(r"/(snyrtivara|leikfong|fatnadur|servara|buildabear|veislurettir|takk-vorur)",))),
        # Products
        Rule(LinkExtractor(allow=(r"/vara/.*-(\d+)",)), callback="parse_sd"),
    )

    item_attributes = {
        "located_in_wikidata": "Q3482054",
    }

    def iter_linked_data(self, response) -> Iterable[dict]:
        next_data_script = response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()
        if next_data_script:
            try:
                data = json.loads(next_data_script)
                product = data.get("props", {}).get("pageProps", {}).get("prefetchedProduct")
                if product:
                    # Map Next.js hydration data to pseudo JSON-LD
                    ld_item = {
                        "@type": "Product",
                        "name": product.get("name"),
                        "brand": product.get("brand"),
                        "sku": product.get("sku"),
                        "image": product.get("image", {}).get("url") if isinstance(product.get("image"), dict) else None,
                        "offers": {
                            "@type": "Offer",
                            "price": product.get("priceMin") or product.get("regularPrice"),
                            "priceCurrency": "ISK",
                            "availability": "https://schema.org/InStock"
                            if product.get("stockStatus") == "IN_STOCK"
                            else "https://schema.org/OutOfStock",
                        },
                        "description": product.get("description"),
                    }
                    yield ld_item
            except (json.JSONDecodeError, KeyError, TypeError):
                pass

        yield from super().iter_linked_data(response)

    def post_process_item(self, item: Product, response, ld_data):
        if ld_data.get("sku"):
            item["ref"] = ld_data["sku"]

        # If brand is not found in LD, try to extract from the prefetchedProduct structure
        # (already handled in iter_linked_data mapping)

        yield item
