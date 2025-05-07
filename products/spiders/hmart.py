from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class HmartSpider(SitemapSpider, StructuredDataSpider):
    name = "hmart"
    allowed_domains = ["hmart.com"]
    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q5636306",
                "name": "H Mart",
            }
        }
    }

    sitemap_urls = ["https://www.hmart.com/robots.txt"]
    sitemap_rules = [
        # https://www.hmart.com/tempura-udon-cup-noodle-cup-2-6oz-75g--6-cups/p
        (r"https://www.hmart.com/[\w-]+/p", "parse_sd"),
    ]
