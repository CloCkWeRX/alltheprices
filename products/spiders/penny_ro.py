import json
import logging
from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST

logger = logging.getLogger(__name__)


class PennyROSpider(SitemapSpider, StructuredDataSpider):
    """
    Scraper for PENNY Romania.
    https://www.penny.ro/

    Sample output:
    {
        "name": "LA DORNA SMANTANA  DE GATIT 32% GRASIME",
        "website": "https://www.penny.ro/products/la-dorna-smantana-de-gatit-32-grasime-rr913069",
        "image": "https://images.cdn.europe-west1.gcp.commercetools.com/3dd00c6e-62c7-4330-9c1a-0067ba317084/RR-913069-1543276665-IFMH1opD.jpg",
        "ref": "RR-913069",
        "sku": "RR-913069",
        "offers": [
            {
                "@type": "Offer",
                "availability": "https://schema.org/InStock",
                "price": 7.49,
                "priceCurrency": "LEI",
                "priceValidUntil": "2026-07-28T00:00:00.000Z",
                "validFrom": "2026-07-22T00:00:00.000Z",
                "validThrough": "2026-07-28T00:00:00.000Z"
            }
        ],
        "proof_currency": "RON",
        "price": 7.49,
        "located_in_wikidata": "Q284688"
    }
    """

    name = "penny_ro"
    allowed_domains = ["penny.ro"]
    sitemap_urls = ["https://www.penny.ro/sitemap.xml"]
    sitemap_rules = [
        (r"/products/.*-(rr\d+)$", "parse_sd"),
    ]

    custom_settings = {
        "USER_AGENT": FIREFOX_LATEST,
        "ROBOTSTXT_OBEY": False,
    }

    item_attributes = {
        "proof_currency": "RON",
        "located_in_wikidata": "Q284688",
    }

    def iter_linked_data(self, response):
        """
        Overridden to support children attribute in application/ld+json scripts.
        """
        # First, try to fetch standard JSON-LD
        for ld_obj in super().iter_linked_data(response):
            yield ld_obj

        # Next, try to fetch children attribute on application/ld+json scripts
        scripts = response.xpath('//script[@type="application/ld+json"]/@children').getall()
        for script_val in scripts:
            try:
                ld_obj = json.loads(script_val, strict=False)
            except Exception:
                logger.debug(f"Failed to decode children attribute as JSON: {script_val[:100]}")
                continue

            if isinstance(ld_obj, dict):
                if "@graph" in ld_obj:
                    yield from filter(None, ld_obj["@graph"])
                else:
                    yield ld_obj
            elif isinstance(ld_obj, list):
                yield from filter(None, ld_obj)

    def post_process_item(self, item, response, ld_data):
        if item.get("offers"):
            price = item["offers"][0].get("price")
            if price:
                try:
                    item["price"] = float(price)
                except Exception:
                    pass
        yield item
