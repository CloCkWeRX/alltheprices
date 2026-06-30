import html
import json
import re
from typing import Iterable

from scrapy import Request
from scrapy.spiders import SitemapSpider

from products.linked_data_parser import LinkedDataParser
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class NaivasKESpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Naivas (Kenya).
    Extracts product data from Schema.org Product data in JSON-LD.
    Uses Playwright to bypass Cloudflare and handle JavaScript-rendered content.

    Sample output:
    {
      "name": "Golden Drop Vegetable Oil 5Ltr",
      "website": "https://www.naivas.online/golden-drop-vegetable-oil-5ltr",
      "ref": "N081793",
      "image": "https://d16zmt6hgq1jhj.cloudfront.net/product/35710/WUmXsMtfrHVTZZjB6dTr7NIClri95yujMguV7VZG.png",
      "offers": [
        {
          "@type": "Offer",
          "priceCurrency": "KES",
          "price": "1199.0000",
          "availability": "https://schema.org/InStock"
        }
      ],
      "extras": {
        "seller": {
          "@type": "Organization",
          "@id": "https://www.wikidata.org/wiki/Q18379067",
          "name": "Naivas Limited"
        }
      }
    }
    """

    name = "naivas_ke"
    allowed_domains = ["naivas.online"]
    sitemap_urls = ["https://www.naivas.online/sitemap-products.xml"]
    # All URLs in sitemap-products.xml are either sub-sitemaps or products.
    # Pattern is generally /[slug]. We exclude .xml to avoid matching sub-sitemaps as products.
    sitemap_rules = [
        (r"sitemap-products-\d+\.xml", "parse_sitemap_recursive"),
        (r"/([^/.]+)$", "parse_sd"),
    ]

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
    }

    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q18379067",
                "name": "Naivas Limited",
            }
        }
    }

    def start_requests(self):
        for url in self.sitemap_urls:
            yield Request(url, callback=self._parse_sitemap, meta={"playwright": True})

    def parse_sitemap_recursive(self, response):
        yield from self._parse_sitemap(response)

    def _parse_sitemap(self, response):
        """
        Use Playwright for all sitemap requests because they are protected by Cloudflare.
        """
        for request_or_item in super()._parse_sitemap(response):
            if isinstance(request_or_item, Request):
                request_or_item.meta["playwright"] = True
                yield request_or_item
            else:
                yield request_or_item

    def iter_linked_data(self, response) -> Iterable[dict]:
        """
        Naivas embeds HTML-escaped JSON-LD.
        """
        lds = response.xpath('//script[@type="application/ld+json"]//text()').getall()
        for ld in lds:
            decoded_ld = html.unescape(ld)
            try:
                ld_obj = json.loads(decoded_ld, strict=False)
            except (json.decoder.JSONDecodeError, ValueError):
                continue

            objs = []
            if isinstance(ld_obj, dict):
                if "@graph" in ld_obj:
                    objs.extend(filter(None, ld_obj["@graph"]))
                else:
                    objs.append(ld_obj)
            elif isinstance(ld_obj, list):
                objs.extend(filter(None, ld_obj))

            for obj in objs:
                if not obj.get("@type"):
                    continue

                types = obj["@type"]
                if not isinstance(types, list):
                    types = [types]

                types = [LinkedDataParser.clean_type(t) for t in types]

                for wanted_types in self.wanted_types:
                    if isinstance(wanted_types, list):
                        if all(wanted in types for wanted in wanted_types):
                            yield obj
                    elif wanted_types in types:
                        yield obj
