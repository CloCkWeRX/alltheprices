from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class EverPHSpider(SitemapSpider, StructuredDataSpider):
    name = "ever_ph"
    allowed_domains = ["ever.ph"]
    item_attributes = {
        "extras": {
            "seller": {"@type": "Organization", "@id": "https://www.wikidata.org/wiki/Q120684300", "name": "Ever"}
        }
    }

    sitemap_urls = ["https://ever.ph/robots.txt"]
    sitemap_rules = [
        (r"https://ever.ph/products/(.*)", "parse_sd"),
    ]
