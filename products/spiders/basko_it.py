import re
from scrapy import Request
from scrapy.spiders import SitemapSpider
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST

class BaskoITSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Basko (Italy).
    Extracts product data from rendered SPA pages.
    Uses Playwright to handle the single-page application.
    Wikidata: Q136464609 (Basko Supermercati)

    Sample output:
    {
        "name": "PERCORSI DI GUSTO PRIMIA Passata di pomodoro 680 GR",
        "website": "https://www.basko.it/product/percorsi-di-gusto-primia-passata-di-pomodoro-680-gr",
        "image": "https://www.basko.it/photo/2025/03/12/34/main/photo/pim-20132-1-main-20250219-193017.jpg",
        "ref": "20132",
        "sku": "20132",
        "brand": "PERCORSI DI GUSTO PRIMIA",
        "located_in_wikidata": "Q136464609",
        "brand_wikidata": "Q136464609"
    }
    """

    name = "basko_it"
    allowed_domains = ["basko.it"]
    sitemap_urls = ["https://www.basko.it/sitemap.xml"]
    sitemap_rules = [(r"/product/([^/]+)$", "parse_sd")]

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

    item_attributes = {
        "located_in_wikidata": "Q136464609",
        "brand_wikidata": "Q136464609",
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
        item["located_in_wikidata"] = "Q136464609"
        item["brand_wikidata"] = "Q136464609"

        # StructuredDataSpider might not get the brand name if it's empty in JSON-LD
        if not item.get("brand") and ld_data.get("brand"):
            brand_data = ld_data["brand"]
            if isinstance(brand_data, dict):
                item["brand"] = brand_data.get("name")
            elif isinstance(brand_data, str):
                item["brand"] = brand_data

        # If brand is still empty or looks like marketing text, try to extract it from the name
        if item.get("name"):
            name = item["name"]
            # Basko often has BRAND in caps at the beginning of the name
            first_word = name.split(" ")[0]
            if not item.get("brand") or len(item["brand"]) > 30 or any(c in item["brand"] for c in "0123456789%"):
                if first_word.isupper() and len(first_word) > 1:
                    item["brand"] = first_word

        # Price is currently 0 in JSON-LD, so we don't promote it to avoid incorrect data.
        if item.get("price") == 0:
            item.pop("price", None)
            item.pop("proof_currency", None)

        if "offers" in item:
            for offer in item["offers"]:
                if offer.get("price") == 0:
                    offer.pop("price", None)
                    offer.pop("priceCurrency", None)

        yield item
