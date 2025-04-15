from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class LongdanGBSpider(SitemapSpider, StructuredDataSpider):
    name = "longdan_gb"
    allowed_domains = ["longdan.co.uk"]
    item_attributes = {
        "extras": {
            "seller": {"@type": "Organization", "@id": "https://www.wikidata.org/wiki/Q111462402", "name": "Longdan"}
        }
    }

    sitemap_urls = ["https://longdan.co.uk/sitemap.xml"]
    sitemap_rules = [
        (r"https://longdan.co.uk/products/[\w-]+", "parse_sd"),
    ]
