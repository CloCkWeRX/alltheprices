from scrapy import Request
from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class CarrefoursaTRSpider(SitemapSpider, StructuredDataSpider):
    """
    CarrefourSA Turkey spider.
    Wikidata: Q28870164
    Bypasses Cloudflare using Playwright.

    Sample output:
    {
        "@context": "https://schema.org/",
        "@type": "Product",
        "name": "Tat Mayonez 330 g",
        "image": "https://reimg-carrefour.mncdn.com/mnresize/600/600/productimage/30096970/30096970_0_MC/8801931395122_1600424564245.jpg",
        "description": "Tat Mayonez 330 g",
        "sku": "30096970",
        "gtin": "8690644243105",
        "offers": {
            "@type": "Offer",
            "url": "https://www.carrefoursa.com/tat-mayonez-330-g-p-30096970",
            "priceCurrency": "TRY",
            "price": "54.50",
            "availability": "https://schema.org/InStock"
        }
    }
    """

    name = "carrefoursa_tr"
    allowed_domains = ["carrefoursa.com"]

    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q28870164",
                "name": "CarrefourSA",
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
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        },
    }

    sitemap_urls = ["https://www.carrefoursa.com/sitemap.xml"]
    sitemap_rules = [
        (r"-p-(\d+)$", "parse_sd"),
    ]

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
