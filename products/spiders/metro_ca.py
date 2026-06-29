import re
from scrapy import Request
from scrapy.spiders import SitemapSpider
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class MetroCASpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Metro (Canada).
    Extracts product data from Schema.org Product data.
    Uses Playwright to bypass Cloudflare on product pages.

    Sample output:
    {
        "name": "Orange-Flavoured Carbonated Soft Drink",
        "website": "https://www.metro.ca/en/online-grocery/aisles/beverages/soft-drinks/fruit-flavoured-soda/orange-flavoured-carbonated-soft-drink/p/056000006832",
        "ref": "056000006832",
        "offers": [
            {
                "@type": "Offer",
                "price": "2.49",
                "priceCurrency": "CAD",
                "availability": "https://schema.org/InStock"
            }
        ],
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q1925345",
                "name": "Metro"
            }
        }
    }
    """

    name = "metro_ca"
    allowed_domains = ["metro.ca"]
    sitemap_urls = ["https://www.metro.ca/sitemap.xml"]
    sitemap_rules = [(r"/p/(\d+)$", "parse_sd")]

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
            "Accept-Language": "en-CA,en-US;q=0.9,en;q=0.8,fr-CA;q=0.7,fr;q=0.6",
        },
    }

    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q1925345",
                "name": "Metro",
            }
        }
    }

    def _parse_sitemap(self, response):
        """
        Only use Playwright for product pages to optimize resources.
        """
        for request_or_item in super()._parse_sitemap(response):
            if isinstance(request_or_item, Request):
                # If it's a product page (not another sitemap)
                if any(re.search(rule[0], request_or_item.url) for rule in self.sitemap_rules):
                    request_or_item.meta["playwright"] = True
                yield request_or_item
            else:
                yield request_or_item
