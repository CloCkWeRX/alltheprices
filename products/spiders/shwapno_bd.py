from scrapy import Request
from scrapy.spiders import SitemapSpider

from products.items import Product
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class ShwapnoBDSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Shwapno (Bangladesh).
    Issue #363. Wikidata Q115664015.

    Sample output:
    {
        "name": "Shop Nescafe Classic coffee 50gm (Glass Bottle) at Shwapno.com",
        "website": "https://www.shwapno.com/nescafe-classic-coffee-50gm-glass-bottle",
        "description": "Discover the best Nescafe Classic coffee 50gm (Glass Bottle) on the top e-commerce site in Bangladesh. Shop now for premium quality and unbeatable prices!",
        "image": "https://d2t8nl1y0ie1km.cloudfront.net/images/thumbs/65fa9389115075f231ec4afa_Nescafe-Classic-coffee-50gm-Glass-Bottle_1_550.webp",
        "sku": "2300069",
        "brand": "Nescafe",
        "offers": [
            {
                "@context": "https://schema.org",
                "@type": "Offer",
                "priceCurrency": "BDT",
                "price": 265,
                "priceValidUntil": "2026-07-31T19:58:00",
                "availability": "https://schema.org/InStock"
            }
        ],
        "ref": "2300069",
        "located_in_wikidata": "Q115664015"
    }
    """

    name = "shwapno_bd"
    allowed_domains = ["shwapno.com"]
    sitemap_urls = ["https://www.shwapno.com/sitemap.xml"]
    sitemap_follow = [r"sitemap-products"]

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
        "located_in_wikidata": "Q115664015",
    }

    def _parse_sitemap(self, response):
        for request_or_item in super()._parse_sitemap(response):
            if isinstance(request_or_item, Request):
                # Product pages are usually at the root or near it,
                # but they don't have a specific pattern besides not being category/brand/etc.
                # Since we only follow sitemap-products, we can assume these are products.
                if "sitemap-products" in response.url:
                    request_or_item.meta["playwright"] = True
                yield request_or_item
            else:
                yield request_or_item

    def post_process_item(self, item: Product, response, ld_data):
        if ld_data.get("sku"):
            item["ref"] = ld_data["sku"]

        if brand := ld_data.get("brand"):
            if isinstance(brand, dict):
                item["brand"] = brand.get("name")
            else:
                item["brand"] = brand

        if description := ld_data.get("description"):
            item["description"] = description

        yield item
