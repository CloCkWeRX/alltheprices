import scrapy
from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider
from products.user_agents import CHROME_LATEST


class AsdaSpider(SitemapSpider, StructuredDataSpider):
    """
    Asda (groceries.asda.com) spider extracting products from sitemaps.
    Uses Playwright for product pages to handle JavaScript-rendered structured data and Cloudflare.

    Sample output:
    {
        "name": "Warburtons 6 Sliced Hotdog Rolls",
        "website": "https://groceries.asda.com/product/white-rolls/warburtons-6-sliced-hotdog-rolls/910000425593",
        "description": "6 White Sliced Hot Dog Rolls",
        "image": "https://ui.assets-asda.com/dm/asdagroceries/5012013010115_T1",
        "ref": "910000425593",
        "sku": "910000425593",
        "brand": "Warburtons",
        "price": 1.5,
        "offers": [
            {
                "@type": "Offer",
                "price": 1.5,
                "priceCurrency": "GBP",
                "availability": "https://schema.org/InStock"
            }
        ],
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q297410",
                "name": "Asda"
            }
        }
    }
    """

    name = "asda"
    allowed_domains = ["asda.com"]
    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q297410",
                "name": "Asda",
            }
        }
    }

    # Use a specific product sitemap if possible to avoid full sitemap crawl.
    # From search, asda uses sitemap-product.xml (discovered via common patterns/search).
    sitemap_urls = ["https://groceries.asda.com/sitemap-product.xml"]
    sitemap_rules = [
        (r"/product/.*/(\d+)$", "parse_sd"),
    ]

    custom_settings = {
        "USER_AGENT": CHROME_LATEST,
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "PLAYWRIGHT_LAUNCH_OPTIONS": {"headless": True},
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 60000,
    }

    def _parse_sitemap(self, response):
        """
        Override _parse_sitemap to inject playwright meta into product requests.
        """
        for request in super()._parse_sitemap(response):
            # If the request is for a product page (callback is parse_sd), use playwright
            if request.callback == self.parse_sd:
                request.meta["playwright"] = True
            yield request
