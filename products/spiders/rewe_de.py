import json
import re
from scrapy import Request
from scrapy.spiders import SitemapSpider
from products.items import Product
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class ReweDESpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for REWE (Germany).
    Wikidata: Q169688
    Fixes #468
    """

    name = "rewe_de"
    allowed_domains = ["rewe.de"]
    sitemap_urls = ["https://www.rewe.de/sitemaps/sitemap.xml"]
    sitemap_rules = [
        (r"/shop/p/.*", "parse_sd"),
    ]

    item_attributes = {
        "located_in_wikidata": "Q169688",
    }

    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": FIREFOX_LATEST,
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "PLAYWRIGHT_BROWSER_TYPE": "firefox",
        "PLAYWRIGHT_LAUNCH_OPTIONS": {"headless": True},
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 30000,
        "CONCURRENT_REQUESTS": 2,
        "DOWNLOAD_DELAY": 1.0,
    }

    def sitemap_filter(self, entries):
        for entry in entries:
            if "sitemap-shop-produkte" in entry["loc"]:
                yield entry

    def start_requests(self):
        if hasattr(self, "urls"):
            urls = self.urls.split(",") if isinstance(self.urls, str) else self.urls
            for url in urls:
                yield Request(
                    url,
                    callback=self.parse_sd,
                    meta={"playwright": True},
                )
            return

        for url in self.sitemap_urls:
            yield Request(
                url,
                callback=self._parse_sitemap,
                meta={"playwright": True},
            )

    def _parse_sitemap(self, response):
        for request_or_item in super()._parse_sitemap(response):
            if isinstance(request_or_item, Request):
                request_or_item.meta["playwright"] = True
                yield request_or_item
            else:
                yield request_or_item

    def post_process_item(self, item: Product, response, ld_data, **kwargs):
        # Always set proof_currency to EUR
        item["proof_currency"] = "EUR"

        # Try to extract richer info and price from embedded script productData
        scripts = response.xpath("//script/text()").getall()
        pd = None
        for s in scripts:
            if "productData" in s:
                match = re.search(r"\{\"productData\":.*\}", s)
                if match:
                    try:
                        data = json.loads(match.group(0))
                        pd = data.get("productData", {})
                        break
                    except json.JSONDecodeError:
                        pass

        if pd:
            if not item.get("name") and pd.get("productName"):
                item["name"] = pd.get("productName")

            if not item.get("brand") and pd.get("brandKey"):
                item["brand"] = pd.get("brandKey")

            if not item.get("gtin") and pd.get("gtin"):
                item["gtin"] = str(pd.get("gtin"))

            if not item.get("ref"):
                if pd.get("productId"):
                    item["ref"] = str(pd.get("productId"))
                elif pd.get("articleId"):
                    item["ref"] = str(pd.get("articleId"))

            pricing = pd.get("pricing", {})
            if isinstance(pricing, dict):
                price_cents = pricing.get("price")
                if price_cents is not None and isinstance(price_cents, (int, float)) and price_cents > 0:
                    item["price"] = round(price_cents / 100.0, 2)

                regular_cents = pricing.get("regularPrice")
                if regular_cents is not None and isinstance(regular_cents, (int, float)) and regular_cents > price_cents:
                    item["price_without_discount"] = round(regular_cents / 100.0, 2)

            media = pd.get("mediaInformation")
            if isinstance(media, list) and media:
                for m in media:
                    if isinstance(m, dict) and m.get("mediaUrl") and not item.get("image"):
                        item["image"] = m.get("mediaUrl")

        # Fallback for ref from URL if still missing
        if not item.get("ref"):
            ref_match = re.search(r"/p/.*?/(\d+)$", response.url)
            if ref_match:
                item["ref"] = ref_match.group(1)

        yield item
