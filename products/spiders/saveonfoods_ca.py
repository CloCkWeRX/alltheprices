import re
from scrapy import Request
from scrapy.spiders import SitemapSpider
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class SaveonfoodsCASpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Save-On-Foods (Canada) (Q7427974).
    Fix #391.

    Sample output:
    {
        "name": "Dempster's - 12 Grain Bagels",
        "website": "https://www.saveonfoods.com/product/dempsters-12-grain-bagels-id-00068721704478",
        "ref": "00068721704478",
        "sku": "00068721704478",
        "brand": "Dempster's",
        "offers": [
            {
                "@type": "Offer",
                "price": "5.79",
                "priceCurrency": "CAD",
                "availability": "https://schema.org/InStock"
            }
        ],
        "price": 5.79,
        "proof_currency": "CAD",
        "located_in_wikidata": "Q7427974"
    }
    """

    name = "saveonfoods_ca"
    allowed_domains = ["saveonfoods.com"]
    sitemap_urls = ["https://www.saveonfoods.com/sitemap.xml"]
    sitemap_rules = [(r"/product/.*?id-(\d+)", "parse_sd")]

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

    def post_process_item(self, item, response, ld_data):
        item["located_in_wikidata"] = "Q7427974"

        # The price extracted from JSON-LD might contain a "$" sign, so we need to clean it up.
        if not item.get("price") or not item.get("proof_currency"):
            offers = ld_data.get("offers", [])
            if isinstance(offers, dict):
                offers = [offers]

            for offer in offers:
                if offer.get("price") and not item.get("price"):
                    item["price"] = offer["price"]
                if offer.get("priceCurrency") and not item.get("proof_currency"):
                    item["proof_currency"] = offer["priceCurrency"]

                if item.get("price") and item.get("proof_currency"):
                    break

        if item.get("price") is not None:
            try:
                # Clean price string (e.g. remove "$" or trailing spaces)
                price_str = str(item["price"]).replace("$", "").replace(",", ".").strip()
                item["price"] = float(price_str)
            except ValueError:
                pass

        if not item.get("proof_currency"):
            item["proof_currency"] = "CAD"

        yield item
