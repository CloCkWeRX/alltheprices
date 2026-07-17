import re

from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class HarrisFarmAUSpider(SitemapSpider, StructuredDataSpider):
    name = "harris_farm_au"
    allowed_domains = ["www.harrisfarm.com.au"]
    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q5664888",
                "name": "Harris Farm Markets",
            }
        }
    }

    sitemap_urls = ["https://www.harrisfarm.com.au/robots.txt"]
    sitemap_rules = [
        (r"https://www.harrisfarm.com.au/products/[\w-]+", "parse_sd"),
    ]

    def post_process_item(self, item, response, ld_data):
        image_url = item.get("image")
        if image_url:
            match = re.search(r"GTIN(\d{8,14})", image_url, re.IGNORECASE)
            if match:
                item["gtin"] = match.group(1)
        yield from super().post_process_item(item, response, ld_data)
