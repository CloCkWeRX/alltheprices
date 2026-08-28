import re
from scrapy import Request
from scrapy.spiders import SitemapSpider
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class BodegaaurreraMXSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Bodega Aurrera (Mexico).
    Extracts product data from Schema.org Product data.
    Uses Playwright to bypass Akamai Bot Protection.

    Fixes #477

    Sample output:
    {
        "name": "Aceite Comestible Puro de Soya Bodega Aurrera 800 ml",
        "website": "https://www.bodegaaurrera.com.mx/ip/aceites-comestibles/aceite-comestible-puro-de-soya-bodega-aurrera-800-ml/00750179166567",
        "ref": "00750179166567",
        "sku": "00750179166567",
        "brand": "Bodega Aurrera",
        "image": "https://i5.walmartimages.com/asr/example.jpeg",
        "offers": [
            {
                "@type": "Offer",
                "price": "32.00",
                "priceCurrency": "MXN",
                "availability": "https://schema.org/InStock",
                "itemCondition": "https://schema.org/NewCondition"
            }
        ],
        "located_in_wikidata": "Q3365858"
    }
    """

    name = "bodegaaurrera_mx"
    allowed_domains = ["bodegaaurrera.com.mx", "walmart.com.mx"]
    sitemap_urls = ["https://www.bodegaaurrera.com.mx/siteindex.xml"]
    sitemap_rules = [(r"/ip/.*", "parse_sd")]

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
        "CONCURRENT_REQUESTS": 2,
        "DOWNLOAD_DELAY": 1.5,
        "DEFAULT_REQUEST_HEADERS": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "es-MX,es;q=0.9,en;q=0.8",
        },
    }

    located_in_wikidata = "Q3365858"

    def sitemap_filter(self, entries):
        """
        Filter sitemap entries to only yield product sitemaps.
        """
        for entry in entries:
            loc = entry.get("loc", "")
            if "productSitemap" in loc or "/ip/" in loc:
                yield entry

    def start_requests(self):
        # Allow testing a single URL if specified
        if hasattr(self, "urls"):
            urls = self.urls.split(",") if isinstance(self.urls, str) else self.urls
            for url in urls:
                yield Request(url, self.parse_sd, meta={"playwright": True})
            return

        for url in self.sitemap_urls:
            # Download initial sitemaps with standard Scrapy (no playwright needed for XML)
            yield Request(url, self._parse_sitemap)

    def _parse_sitemap(self, response):
        """
        Ensure product detail requests from the sitemap use Playwright.
        """
        for request_or_item in super()._parse_sitemap(response):
            if isinstance(request_or_item, Request):
                if re.search(r"/ip/.*", request_or_item.url):
                    request_or_item.meta["playwright"] = True
                yield request_or_item
            else:
                yield request_or_item

    def post_process_item(self, item, response, ld_data, **kwargs):
        if not item.get("offers"):
            yield item
            return

        for offer in item.get("offers", []):
            if isinstance(offer, dict):
                offer["priceCurrency"] = "MXN"

        yield item
