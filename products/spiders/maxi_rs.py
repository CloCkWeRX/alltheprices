import re
from scrapy import Request
from scrapy.spiders import SitemapSpider
from scrapy.utils.sitemap import Sitemap
from scrapy_playwright.page import PageMethod

from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class MaxiRSSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Maxi (Serbia).
    Extracts product data from Schema.org Product data.
    Uses Playwright to render JavaScript and JSON-LD structured data.

    Sample output:
    {
        "name": "losion za negu kozne obuce Erdal 500ml",
        "website": "https://www.maxi.rs/Kucjna-hemija-i-papirna-galanterija/Sredstva-i-oprema-za-chishcjenje/Sredstva-za-chishcjenje/Sredstva-za-obucju/losion-za-negu-kozne-obuce-Erdal-500ml/p/7176736",
        "ref": "7176736",
        "offers": [
            {
                "@type": "Offer",
                "availability": "https://schema.org/InStock",
                "priceSpecification": {
                    "@type": "UnitPriceSpecification",
                    "price": 598.99,
                    "priceCurrency": "RSD"
                }
            }
        ],
        "price": 598.99,
        "proof_currency": "RSD",
        "located_in_wikidata": "Q117070188",
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q117070188",
                "name": "Maxi"
            }
        }
    }
    """

    name = "maxi_rs"
    allowed_domains = ["maxi.rs"]
    sitemap_urls = [
        "https://www.maxi.rs/sitemap/delhaizesitemapindex.xml",
    ]
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
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "sr-RS,sr;q=0.9,en-US;q=0.8,en;q=0.7",
        },
    }

    item_attributes = {
        "located_in_wikidata": "Q117070188",
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q117070188",
                "name": "Maxi",
            }
        },
    }

    def _parse_sitemap(self, response):
        if response.url.endswith(".xml") or response.url.endswith(".xml.gz"):
            body = self._get_sitemap_body(response)
            if body is None:
                self.logger.warning(f"Could not get sitemap body for {response.url}")
                return

            s = Sitemap(body)
            if s.type == "sitemapindex":
                for loc in iterloc(s):
                    yield Request(loc, callback=self._parse_sitemap)
            elif s.type == "urlset":
                for d in s:
                    loc = d["loc"]
                    for rule_re, callback in self.sitemap_rules:
                        if re.search(rule_re, loc):
                            yield Request(
                                loc,
                                callback=self.parse_sd,
                                meta={
                                    "playwright": True,
                                    "playwright_page_methods": [
                                        PageMethod(
                                            "wait_for_selector",
                                            'script[type="application/ld+json"]',
                                            state="attached",
                                            timeout=10000,
                                        )
                                    ],
                                },
                            )
                            break
        else:
            yield from super()._parse_sitemap(response)

    def post_process_item(self, item, response, ld_data):
        ref_match = re.search(r"/p/(\d+)$", response.url)
        if ref_match:
            item["ref"] = ref_match.group(1)

        if "offers" in item and item["offers"]:
            offers = item["offers"]
            if isinstance(offers, list):
                offer = offers[0]
            else:
                offer = offers

            if "price" in offer:
                item["price"] = float(offer["price"])
            elif "priceSpecification" in offer:
                ps = offer["priceSpecification"]
                if isinstance(ps, list):
                    ps = ps[0]
                if "price" in ps:
                    item["price"] = float(ps["price"])
                if "priceCurrency" in ps:
                    item["proof_currency"] = ps["priceCurrency"]

            if "priceCurrency" in offer:
                item["proof_currency"] = offer["priceCurrency"]

        if not item.get("proof_currency"):
            item["proof_currency"] = "RSD"

        return item


def iterloc(it, iternext="loc"):
    for d in it:
        yield d[iternext]
