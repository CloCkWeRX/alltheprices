import re
from scrapy import Request
from scrapy.spiders import SitemapSpider
from scrapy.utils.sitemap import Sitemap
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class DelhaizeBESpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Delhaize (Belgium).
    Extracts product data from Schema.org Product data.
    Uses Playwright to bypass JavaScript-only rendering of structured data.

    Sample output:
    {
        "name": "Pindas",
        "website": "https://www.delhaize.be/nl/shop/Zoetigheden-en-zoute-snacks/Snacks/Pindas/Pindas/p/S20475",
        "ref": "S20475",
        "offers": [
            {
                "@type": "Offer",
                "price": "1.25",
                "priceCurrency": "EUR",
                "availability": "https://schema.org/InStock"
            }
        ],
        "price": 1.25,
        "proof_currency": "EUR",
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q1184173",
                "name": "Delhaize"
            }
        }
    }
    """

    name = "delhaize_be"
    allowed_domains = ["delhaize.be"]
    sitemap_urls = [
        "https://www.delhaize.be/sitemap/delhaizesitemapindex.xml",
        "https://www.delhaize.be/sitemapnl/delhaizesitemapindex.xml",
    ]
    sitemap_rules = [(r"/p/([A-Z0-9]+)$", "parse_sd")]

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
            "Accept-Language": "nl-BE,nl;q=0.9,fr-BE;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5",
        },
    }

    item_attributes = {
        "located_in_wikidata": "Q1184173",
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q1184173",
                "name": "Delhaize",
            }
        },
    }

    def _parse_sitemap(self, response):
        """
        Handle Delhaize sitemaps where <loc> can be empty and URLs are in <xhtml:link>.
        """
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
                from lxml import etree

                root = etree.fromstring(body)
                namespaces = {
                    "s": "http://www.sitemaps.org/schemas/sitemap/0.9",
                    "xhtml": "http://www.w3.org/1999/xhtml",
                }
                for url_node in root.xpath("//s:url", namespaces=namespaces):
                    locs = url_node.xpath("s:loc/text()", namespaces=namespaces)
                    loc = locs[0] if locs else ""
                    if not loc:
                        # Try alternate links
                        alternate_locs = url_node.xpath(
                            'xhtml:link[@rel="alternate"]/@href', namespaces=namespaces
                        )
                        # Pick one, preferably nl or fr
                        for aloc in alternate_locs:
                            if "/nl/" in aloc or "/fr/" in aloc:
                                loc = aloc
                                break
                        if not loc and alternate_locs:
                            loc = alternate_locs[0]

                    if loc:
                        for rule_re, callback in self.sitemap_rules:
                            if re.search(rule_re, loc):
                                yield Request(
                                    loc, callback=self.parse_sd, meta={"playwright": True}
                                )
                                break
        else:
            yield from super()._parse_sitemap(response)

    def post_process_item(self, item, response, ld_data):
        """
        Promote price and currency from offers.
        """
        if "offers" in item and item["offers"]:
            offers = item["offers"]
            if isinstance(offers, list):
                offer = offers[0]
            else:
                offer = offers

            if "price" in offer:
                item["price"] = offer["price"]
            elif "priceSpecification" in offer:
                ps = offer["priceSpecification"]
                if isinstance(ps, list):
                    ps = ps[0]
                if "price" in ps:
                    item["price"] = ps["price"]
                if "priceCurrency" in ps:
                    item["proof_currency"] = ps["priceCurrency"]

            if "priceCurrency" in offer:
                item["proof_currency"] = offer["priceCurrency"]

        yield item


def iterloc(it, iternext="loc"):
    for d in it:
        yield d[iternext]
