from scrapy import Request
from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class BigcTHSpider(SitemapSpider, StructuredDataSpider):
    """
    Big C Thailand spider.
    Bypasses Cloudflare using Playwright.

    Sample output:
    {
        "@context": "https://schema.org/",
        "@type": "Product",
        "name": "โค้ก น้ำอัดลม รสออริจินัล สูตรน้ำตาลน้อยกว่า 1 ล.",
        "image": "https://st.bigc-cs.com/cdn-cgi/image/format=webp,quality=90/public/media/catalog/product/10/88/8851959149010/thumbnail/8851959149010_1-20260521161854-.jpg",
        "description": "...",
        "sku": "8851959149010",
        "gtin": "8851959149010",
        "brand": {"@type": "Brand", "name": "โค้ก"},
        "offers": {
            "@type": "Offer",
            "url": "https://www.bigc.co.th/product/coca-cola-coke-original-less-sugar-1-l-8851959149010.68759",
            "priceCurrency": "THB",
            "price": "25.00",
            "availability": "InStock"
        }
    }
    """

    name = "bigc_th"
    allowed_domains = ["bigc.co.th"]

    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q858665",
                "name": "Big C Thailand",
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
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
        "DEFAULT_REQUEST_HEADERS": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9,th;q=0.8",
        },
    }

    sitemap_urls = ["https://www.bigc.co.th/sitemaps/sitemap.xml"]
    sitemap_rules = [
        (r"/product/.*\.(\d+)$", "parse_sd"),
    ]

    def start_requests(self):
        for url in self.sitemap_urls:
            yield Request(url, self._parse_sitemap, meta={"playwright": True})

    def _parse_sitemap(self, response):
        """
        SitemapSpider's _parse_sitemap usually handles the sitemap XML.
        We need to make sure subsequent requests also use Playwright.
        """
        # Call the original _parse_sitemap but we need to wrap the resulting requests
        # to include playwright=True in meta.
        for request_or_item in super()._parse_sitemap(response):
            if isinstance(request_or_item, Request):
                request_or_item.meta["playwright"] = True
                yield request_or_item
            else:
                yield request_or_item
