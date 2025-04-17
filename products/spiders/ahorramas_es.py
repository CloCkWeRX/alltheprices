from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class AhorramasESSpider(SitemapSpider, StructuredDataSpider):
    name = "ahorramas_es"
    allowed_domains = ["ahorramas.com"]
    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q5047480",
                "name": "Ahorramas",
            }
        }
    }

    sitemap_urls = ["https://www.ahorramas.com/robots.txt"]
    sitemap_rules = [
        (r"https://www.ahorramas.com/[\w-]+.html", "parse_sd"),
    ]
