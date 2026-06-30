import re
from scrapy import Request
from scrapy.http import Response
from scrapy.spiders import SitemapSpider
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class MasoutisGRSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Masoutis (Greece).
    Wikidata: Q6783887
    The site is a SPA and product data is embedded in ld+json after rendering.

    Sample output:
    {
        "name": "Hemo Ρόφημα Σοκολάτας 400γρ.",
        "website": "https://www.masoutis.gr/categories/item/hemo-rofhma-sokolatas-400gr?0015909",
        "description": "Μια μόνο κουταλιά HΕΜΟ, σε ένα ποτήρι γάλα, δίνει περίπου το 1/3 των απαραίτητων βιταμινών και μεταλλικών στοιχείων που χρειάζεται καθημερινά ο οργανισμός. Το ΗΕΜΟ περιέχει 11 βιταμίνες, 4 μεταλλικά στοιχεία και βύνη!",
        "ref": "0015909",
        "brand": "HEMO",
        "offers": [
            {
                "@type": "Offer",
                "priceCurrency": "EUR",
                "price": 4.15,
                "availability": "https://schema.org/InStock",
                "url": "https://www.masoutis.gr/categories/item/hemo-rofhma-sokolatas-400gr?0015909"
            }
        ],
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q6783887",
                "name": "Masoutis"
            }
        }
    }
    """

    name = "masoutis_gr"
    allowed_domains = ["masoutis.gr"]
    sitemap_urls = ["https://www.masoutis.gr/images/sitemapthree.xml"]
    sitemap_rules = [(r"/categories/item/.*?\?(\d+)=?$", "parse_sd")]

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
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q6783887",
                "name": "Masoutis",
            }
        }
    }

    def _parse_sitemap(self, response):
        for request_or_item in super()._parse_sitemap(response):
            if isinstance(request_or_item, Request):
                if any(re.search(rule[0], request_or_item.url) for rule in self.sitemap_rules):
                    request_or_item.meta["playwright"] = True
                    request_or_item.meta["playwright_include_page"] = False
                yield request_or_item
            else:
                yield request_or_item

    def get_ref(self, url: str, response: Response = None) -> str:
        for rule in self.sitemap_rules:
            if match := re.search(rule[0], url):
                return match.group(1)
        return super().get_ref(url, response)
