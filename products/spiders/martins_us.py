import json
from scrapy import Request
from products.structured_data_spider import StructuredDataSpider

class MartinsUSSpider(StructuredDataSpider):
    """
    Martin's Super Markets (United States) spider.
    Uses Freshop API for product discovery and extracts JSON-LD from product pages.
    Wikidata: Q7573912 (SpartanNash - parent)

    Sample output structured data:
    {
        "extras": {
            "seller": {
                "@id": "https://www.wikidata.org/wiki/Q7573912",
                "@type": "Organization",
                "name": "Martin's Super Markets"
            }
        },
        "image": "https://images.freshop.ncrcloud.com/1491/cd8190961b5086661b9a9cdd8887687a_large.png",
        "name": "Green Bell Peppers",
        "offers": [
            {
                "@type": "Offer",
                "price": "0.99",
                "priceCurrency": "USD"
            }
        ],
        "ref": "4065",
        "website": "https://www.martinsgroceriestogo.com/shop/produce/green_bell_peppers/p/1491"
    }
    """

    name = "martins_us"
    allowed_domains = ["martinsgroceriestogo.com", "api.freshop.ncrcloud.com"]

    # Store ID 5445 (Martins - Emerald) seems to have most products (~150k)
    base_api_url = "https://api.freshop.ncrcloud.com/1/products?app_key=martins&store_id=5445&limit=100"

    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q7573912",
                "name": "Martin's Super Markets",
            }
        }
    }

    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
        "ROBOTSTXT_OBEY": False,
    }

    def start_requests(self):
        yield Request(self.base_api_url + "&offset=0", callback=self.parse_discovery)

    def parse_discovery(self, response):
        data = json.loads(response.text)
        items = data.get("items", [])

        for item in items:
            if url := item.get("canonical_url"):
                yield Request(url, callback=self.parse_sd)

        if items:
            # Handle pagination
            current_offset = int(response.url.split("offset=")[1])
            new_offset = current_offset + 100

            if new_offset < data.get("total", 0):
                 yield Request(self.base_api_url + f"&offset={new_offset}", callback=self.parse_discovery)
