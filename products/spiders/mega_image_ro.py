import re
from scrapy import Request
from scrapy.spiders import SitemapSpider
from scrapy.utils.sitemap import Sitemap
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class MegaImageROSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Mega Image (Romania).
    Extracts product data from Schema.org Product data.
    Uses Playwright to bypass JavaScript-only rendering of structured data.

    Sample output:
    {
        "name": "Branza cottage 4% grasime",
        "website": "https://www.mega-image.ro/Lactate-si-oua/Branzeturi/Branza-proaspata/Branza-cottage-4-grasime/p/27471",
        "description": "Granule de branza cu smantana.",
        "brand": "Olympus",
        "ref": "27471",
        "offers": [
            {
                "@type": "Offer",
                "price": "7.39",
                "priceCurrency": "RON",
                "availability": "https://schema.org/InStock"
            }
        ],
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q6808085",
                "name": "Mega Image"
            }
        }
    }
    """

    name = "mega_image_ro"
    allowed_domains = ["mega-image.ro"]
    sitemap_urls = ["https://www.mega-image.ro/sitemap/delhaizesitemapindex.xml"]
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
            "Accept-Language": "ro-RO,ro;q=0.9,en-US;q=0.8,en;q=0.7",
        },
    }

    item_attributes = {
        "brand_wikidata": "Q6808085",
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q6808085",
                "name": "Mega Image",
            }
        }
    }

    def _parse_sitemap(self, response):
        """
        Handle Mega Image sitemaps where <loc> is empty and URLs are in <xhtml:link>.
        """
        if response.url.endswith(".xml") or response.url.endswith(".xml.gz"):
            body = self._get_sitemap_body(response)
            if body is None:
                self.logger.warning(f"Could not get sitemap body for {response.url}")
                return

            s = Sitemap(body)
            if s.type == "sitemapindex":
                for loc in iterloc(s):
                    if any(re.search(rule[0], loc) for rule in self.sitemap_rules):
                        yield Request(loc, callback=self.parse_sd, meta={"playwright": True})
                    else:
                        yield Request(loc, callback=self._parse_sitemap)
            elif s.type == "urlset":
                # Special handling for Mega Image urlset
                # Use lxml to extract xhtml:link if loc is empty
                from lxml import etree

                root = etree.fromstring(body)
                # Define namespaces
                namespaces = {
                    "s": "http://www.sitemaps.org/schemas/sitemap/0.9",
                    "xhtml": "http://www.w3.org/1999/xhtml",
                }
                for url_node in root.xpath("//s:url", namespaces=namespaces):
                    loc = url_node.xpath("s:loc/text()", namespaces=namespaces)
                    loc = loc[0] if loc else ""
                    if not loc:
                        # Try alternate link
                        loc = url_node.xpath(
                            'xhtml:link[@rel="alternate"]/@href', namespaces=namespaces
                        )
                        loc = loc[0] if loc else ""

                    if loc:
                        for rule_re, callback in self.sitemap_rules:
                            if re.search(rule_re, loc):
                                yield Request(
                                    loc, callback=self.parse_sd, meta={"playwright": True}
                                )
                                break
        else:
            yield from super()._parse_sitemap(response)


def iterloc(it, iternext="loc"):
    for d in it:
        yield d[iternext]
