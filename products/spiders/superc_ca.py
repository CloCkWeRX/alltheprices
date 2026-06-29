from scrapy import Request
from scrapy.spiders import SitemapSpider
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class SupercCASpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Super C (Canada).
    Extracts product data from Microdata (Schema.org Product).
    Uses Playwright to bypass Cloudflare.

    Sample output:
    {
        "name": "Ananas",
        "website": "https://www.superc.ca/allees/fruits-et-legumes/fruits/avocats-et-fruits-exotiques/ananas/p/4430",
        "ref": "4430",
        "offers": [
            {
                "@type": "Offer",
                "price": "3.99",
                "priceCurrency": "CAD"
            }
        ],
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q3504127",
                "name": "Super C"
            }
        }
    }
    """

    name = "superc_ca"
    allowed_domains = ["superc.ca"]
    sitemap_urls = ["https://www.superc.ca/sitemap.xml"]
    sitemap_rules = [(r"/p/(\d+)", "parse_sd")]

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
                "@id": "https://www.wikidata.org/wiki/Q3504127",
                "name": "Super C",
            }
        }
    }

    def start_requests(self):
        for url in self.sitemap_urls:
            yield Request(url, self._parse_sitemap, meta={"playwright": True})

    def _parse_sitemap(self, response):
        """
        Ensure subsequent requests from the sitemap also use Playwright.
        """
        for request_or_item in super()._parse_sitemap(response):
            if isinstance(request_or_item, Request):
                request_or_item.meta["playwright"] = True
                yield request_or_item
            else:
                yield request_or_item
