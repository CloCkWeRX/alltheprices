from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class DixyRUSpider(SitemapSpider, StructuredDataSpider):
    name = "dixy_ru"
    allowed_domains = ["dixy.ru"]
    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q4161561", 
                "name": "Dixy"
            }
        }
    }
    sitemap_urls = ["https://dixy.ru/sitemap.xml"]
    sitemap_rules = [
        (r"https://dixy.ru/catalog/[\w-]+/[\w-]+/[\d]+/", "parse_sd"),
    ]
