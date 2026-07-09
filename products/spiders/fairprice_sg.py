import json
import re

from scrapy import Request
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from products.items import Product
from products.structured_data_spider import StructuredDataSpider


class FairpriceSGSpider(CrawlSpider, StructuredDataSpider):
    """
    Spider for NTUC FairPrice (Singapore).
    Example item:
    {
        "name": "Coca-Cola Original Taste - Less Sugar",
        "brand": "Coca-Cola",
        "description": "Buy 1 Coca-Cola Original Taste - Less Sugar @ $13.75. Grab now before 8 Jul 2026!",
        "image": "https://media.nedigital.sg/fairprice/fpol/media/images/product/XL/13241340_XL1_20260424.jpg",
        "url": "https://www.fairprice.com.sg/product/coca-cola-original-taste-less-sugar-24-x-320ml-13241340",
        "ref": "13241340",
        "located_in_wikidata": "Q6955519",
        "offers": [
            {
                "@type": "Offer",
                "price": "13.75",
                "priceCurrency": "SGD",
                "availability": "https://schema.org/InStock"
            }
        ]
    }
    """

    name = "fairprice_sg"
    allowed_domains = ["fairprice.com.sg"]
    start_urls = ["https://www.fairprice.com.sg/"]
    json_parser = "chompjs"

    rules = (
        Rule(LinkExtractor(allow=r"/category/")),
        Rule(LinkExtractor(allow=r"/product/.*-(\d+)$"), callback="parse_sd"),
    )

    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "DEFAULT_REQUEST_HEADERS": {
            "Accept-Language": "en-US,en;q=0.9",
        },
    }

    def parse_start_url(self, response, **kwargs):
        # Seed from homepage __NEXT_DATA__
        yield from self._extract_next_data_links(response)

    def _extract_next_data_links(self, response):
        next_data_script = response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()
        if not next_data_script:
            return

        try:
            data = json.loads(next_data_script)
            # Recursively find 'slug' keys
            for slug in self._find_key(data, "slug"):
                if isinstance(slug, str):
                    # Guess if it's a product or category based on pattern (products often have numeric ID at end)
                    if slug.split("-")[-1].isdigit():
                        yield Request(response.urljoin(f"/product/{slug}"), callback=self.parse_sd)
                    else:
                        yield Request(response.urljoin(f"/category/{slug}"))
        except:
            pass

    def _find_key(self, obj, key):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k.lower() == key.lower():
                    yield v
                yield from self._find_key(v, key)
        elif isinstance(obj, list):
            for item in obj:
                yield from self._find_key(item, key)

    def post_process_item(self, item: Product, response, ld_data, **kwargs):
        item["located_in_wikidata"] = "Q6955519"

        if item.get("website") and item["website"].startswith("/"):
            item["website"] = response.urljoin(item["website"])

        if isinstance(item.get("brand"), dict):
            item["brand"] = item["brand"].get("name")

        if item.get("offers"):
            for offer in item["offers"]:
                if not offer.get("priceCurrency"):
                    offer["priceCurrency"] = "SGD"

        # Ref can often be found at the end of the URL if not in LD
        if not item.get("ref") or not item["ref"].isdigit():
            if match := re.search(r"-(\d+)$", response.url):
                item["ref"] = match.group(1)

        yield item
