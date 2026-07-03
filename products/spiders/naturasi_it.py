import re
from scrapy import Request
from scrapy.http import Response
from scrapy.spiders import SitemapSpider
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class NaturasiITSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for NaturaSì (Italy).
    Extracts product data from rendered SPA pages.
    Uses Playwright to handle the single-page application.

    Sample output:
    {
        "name": "Kajal matita occhi grigio 03",
        "website": "https://www.naturasi.it/prodotti/03-kajal-matita-occhi-grigio-purobio-3921",
        "ref": "3921",
        "located_in_wikidata": "Q60840755",
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q60840755",
                "name": "NaturaSì"
            }
        }
    }
    """

    name = "naturasi_it"
    allowed_domains = ["naturasi.it"]
    sitemap_urls = [
        "https://www.naturasi.it/product_0.xml",
        "https://www.naturasi.it/product_1.xml",
        "https://www.naturasi.it/product_2.xml",
        "https://www.naturasi.it/product_3.xml",
        "https://www.naturasi.it/product_4.xml",
        "https://www.naturasi.it/product_5.xml",
        "https://www.naturasi.it/product_6.xml",
    ]
    sitemap_rules = [(r"/prodotti/", "parse_sd")]

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
        "USER_AGENT": FIREFOX_LATEST,
    }

    item_attributes = {
        "located_in_wikidata": "Q60840755",
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q60840755",
                "name": "NaturaSì",
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

    def get_ref(self, url: str, response: Response) -> str:
        # Example URL: https://www.naturasi.it/prodotti/03-kajal-matita-occhi-grigio-purobio-3921
        # The ref seems to be the last numeric part of the slug.
        if match := re.search(r"-(\d+)$", url):
            return match.group(1)
        return super().get_ref(url, response)
