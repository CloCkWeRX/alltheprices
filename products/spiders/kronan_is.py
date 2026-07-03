import json
import re
from typing import Iterable

from scrapy.spiders import SitemapSpider

from products.items import Product
from products.structured_data_spider import StructuredDataSpider


class KronanIsSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Krónan (Iceland).
    Issue #263. Wikidata Q16419327.

    Sample output:
    {
        "brand_wikidata": "Q16419327",
        "image": "https://media.kronan.is/products/117837",
        "name": "Gatorade cool blue",
        "offers": [
            {
                "@type": "Offer",
                "availability": "https://schema.org/InStock",
                "price": 202.0,
                "priceCurrency": "ISK"
            }
        ],
        "ref": "100008747",
        "website": "https://kronan.is/vara/100008747-gatorade-cool-blue"
    }
    """

    name = "kronan_is"
    allowed_domains = ["kronan.is"]
    sitemap_urls = ["https://kronan.is/sitemap.xml"]
    sitemap_rules = [(r"/vara/(\d+)-", "parse_sd")]

    item_attributes = {
        "brand_wikidata": "Q16419327",
    }

    def iter_linked_data(self, response) -> Iterable[dict]:
        # Krónan uses Next.js hydration scripts.
        # Product data is often in self.__next_f.push calls.
        payloads = re.findall(
            r"self\.__next_f\.push\(\[1,\"(.*?)\"\]\)", response.text, re.DOTALL
        )
        for p in payloads:
            if "Product" in p:
                try:
                    # Unescape the string to get valid JSON
                    unescaped = p.encode().decode("unicode_escape")
                    # Next.js payloads often have a numeric prefix like "10:"
                    if ":" in unescaped[:10]:
                        unescaped = unescaped[unescaped.find(":") + 1 :]

                    data = json.loads(unescaped)
                    yield from self._walk_for_product(data)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    continue

        yield from super().iter_linked_data(response)

    def _walk_for_product(self, obj):
        if isinstance(obj, dict):
            if obj.get("@type") == "Product":
                yield obj
            for v in obj.values():
                yield from self._walk_for_product(v)
        elif isinstance(obj, list):
            for item in obj:
                yield from self._walk_for_product(item)
