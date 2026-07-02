import re
from scrapy import Request
from scrapy.spiders import SitemapSpider
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class IperalITSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Iperal (Italy).
    Extracts product data from rendered SPA pages.
    Uses Playwright to handle the single-page application.

    Note: Prices are reported as 0 in the site's JSON-LD when not logged in or
    without a selected store/delivery method.

    Sample output:
    {
        "name": "Fette Biscottate Dorate",
        "website": "https://www.iperalspesaonline.it/product/fette-biscottate-le-dorate-mulino-bianco-g-630",
        "ref": "1403022",
        "located_in_wikidata": "Q3801481",
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q3801481",
                "name": "Iperal"
            }
        }
    }
    """

    name = "iperal_it"
    allowed_domains = ["iperalspesaonline.it"]
    sitemap_urls = ["https://www.iperalspesaonline.it/sitemap_ebsn.xml"]
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
        "located_in_wikidata": "Q3801481",
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q3801481",
                "name": "Iperal",
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
