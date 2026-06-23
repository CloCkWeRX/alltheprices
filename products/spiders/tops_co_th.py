from scrapy import Request
from scrapy.spiders import SitemapSpider

from products.items import Product
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class TopsCOTHSpider(SitemapSpider, StructuredDataSpider):
    """
    Tops Thailand spider.
    Wikidata: Q7825140
    Bypasses Cloudflare using Playwright.

    Sample output:
    {
        "name": "Kani Fresh Crab Stick 250g.",
        "website": "https://www.tops.co.th/en/kani-fresh-crab-stick-250g-8850524100036",
        "image": "https://www.tops.co.th/file-assets/TOPSPIM/web/Image/8850524/KANI-KaniFreshCrabStick250g-8850524100036-1.jpg",
        "ref": "8850524100036",
        "offers": [
            {
                "@type": "Offer",
                "url": "https://www.tops.co.th/en/kani-fresh-crab-stick-250g-8850524100036",
                "priceCurrency": "THB",
                "price": 117,
                "availability": "https://schema.org/OutOfStock"
            }
        ]
    }
    """

    name = "tops_co_th"
    allowed_domains = ["tops.co.th"]

    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q7825140",
                "name": "Tops Thailand",
            }
        }
    }

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
            "Accept-Language": "en-US,en;q=0.5",
        },
    }

    sitemap_urls = ["https://www.tops.co.th/sitemap/sitemap-index.xml"]
    sitemap_rules = [
        (r"/(en|th)/.*-(\d+)$", "parse_sd"),
    ]

    def start_requests(self):
        for url in self.sitemap_urls:
            yield Request(url, self._parse_sitemap, meta={"playwright": True})

    def _parse_sitemap(self, response):
        for request_or_item in super()._parse_sitemap(response):
            if isinstance(request_or_item, Request):
                request_or_item.meta["playwright"] = True
                yield request_or_item
            else:
                yield request_or_item

    def post_process_item(self, item: Product, response, ld_data):
        if item.get("image") and not item["image"].startswith(("http", "/")):
            item["image"] = response.urljoin(item["image"])
        yield from super().post_process_item(item, response, ld_data)
