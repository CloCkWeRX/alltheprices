import re
from scrapy import Request
from scrapy.spiders import SitemapSpider

from products.items import Product
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class PaknsaveNZSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Pak'nSave (New Zealand).
    Wikidata: Q7125348

    Sample output structured data:
    {
        "name": "Original Biscuits",
        "website": "https://www.paknsave.co.nz/shop/product/5001361_ea_000pnsnw?name=original-biscuits",
        "image": "https://www.paknsave.co.nz/shop/product/images/5001361.jpg",
        "ref": "5001361_ea_000pnsnw",
        "brand": "Pams",
        "located_in_wikidata": "Q7125348",
        "price": "2.50",
        "proof_currency": "NZD"
    }
    """

    name = "paknsave_nz"
    allowed_domains = ["paknsave.co.nz"]
    sitemap_urls = ["https://www.paknsave.co.nz/robots.txt"]
    sitemap_rules = [
        (r"shop/product/[\d\w_]+", "parse_sd"),
    ]

    custom_settings = {
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "DOWNLOAD_HANDLERS": {
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "PLAYWRIGHT_BROWSER_TYPE": "firefox",
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 60 * 1000,
        "PLAYWRIGHT_LAUNCH_OPTIONS": {
            "headless": True,
        },
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": FIREFOX_LATEST,
        "DEFAULT_REQUEST_HEADERS": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        },
    }

    item_attributes = {
        "located_in_wikidata": "Q7125348",
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q7125348",
                "name": "PAK'nSAVE",
            }
        },
    }

    def _parse_sitemap(self, response):
        """
        Only use Playwright for product pages to optimize resources.
        """
        for request_or_item in super()._parse_sitemap(response):
            if isinstance(request_or_item, Request):
                if any(re.search(rule[0], request_or_item.url) for rule in self.sitemap_rules):
                    request_or_item.meta["playwright"] = True
                yield request_or_item
            else:
                yield request_or_item

    def post_process_item(self, item: Product, response, ld_data):
        item["located_in_wikidata"] = "Q7125348"
        item["proof_currency"] = "NZD"

        # If price is missing from top-level but present in offers, promote it
        if not item.get("price") and item.get("offers"):
            offers = item["offers"]
            if isinstance(offers, dict):
                offers = [offers]
            if isinstance(offers, list) and len(offers) > 0:
                price = offers[0].get("price")
                if price:
                    item["price"] = price

        yield item
