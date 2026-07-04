import json
import re
from typing import Iterable

from scrapy import Request
from scrapy.spiders import SitemapSpider

from products.items import Product
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class WinmartVNSpider(SitemapSpider, StructuredDataSpider):
    """
    WinMart (Vietnam) spider.
    Issue #270. Wikidata Q60245505.
    """

    name = "winmart_vn"
    allowed_domains = ["winmart.vn"]
    sitemap_urls = ["https://winmart.vn/sitemap.xml"]

    sitemap_rules = [
        (r"--c\d+", "parse_category"),
        (r"/products/[^?]+", "parse_sd"),
    ]

    custom_settings = {
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "DOWNLOAD_HANDLERS": {
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "PLAYWRIGHT_BROWSER_TYPE": "firefox",
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 60 * 1000,
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": FIREFOX_LATEST,
    }

    item_attributes = {
        "located_in_wikidata": "Q60245505",
    }

    def _parse_sitemap(self, response):
        for request_or_item in super()._parse_sitemap(response):
            if isinstance(request_or_item, Request):
                if any(re.search(rule[0], request_or_item.url) for rule in self.sitemap_rules if rule[1] == "parse_category"):
                    request_or_item.meta["playwright"] = True
                yield request_or_item
            else:
                yield request_or_item

    def parse_category(self, response):
        # Discover product links from the rendered category page
        product_links = response.css('a[href*="/products/"]::attr(href)').getall()
        for link in product_links:
            yield response.follow(link, callback=self.parse_sd)

    def iter_linked_data(self, response) -> Iterable[dict]:
        next_data_script = response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()
        if next_data_script:
            try:
                data = json.loads(next_data_script)
                product = data.get("props", {}).get("pageProps", {}).get("product")
                if product:
                    ld_item = {
                        "@type": "Product",
                        "name": product.get("name"),
                        "brand": product.get("brandName"),
                        "sku": product.get("sku"),
                        "image": product.get("image") or product.get("mediaUrl"),
                        "offers": {
                            "@type": "Offer",
                            "price": product.get("salePrice") or product.get("price"),
                            "priceCurrency": "VND",
                            "availability": "https://schema.org/InStock" if product.get("quantity", 0) > 0 else "https://schema.org/OutOfStock",
                        },
                    }
                    if product.get("barcode"):
                        ld_item["gtin"] = product["barcode"]

                    yield ld_item
            except (json.JSONDecodeError, KeyError, TypeError):
                pass

        yield from super().iter_linked_data(response)

    def post_process_item(self, item: Product, response, ld_data):
        if ld_data.get("sku"):
            item["ref"] = ld_data["sku"]

        if item.get("gtin"):
            gtin = str(item["gtin"])
            if len(gtin) == 13:
                item["gtin13"] = gtin
            elif len(gtin) == 12:
                item["gtin12"] = gtin

        yield item
