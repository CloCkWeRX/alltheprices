from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class JayagrocerSpider(SitemapSpider, StructuredDataSpider):
    name = "jayagrocer"
    allowed_domains = ["jayagrocer.com"]
    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q116275052",
                "name": "Jaya Grocer",
            }
        }
    }

    sitemap_urls = ["https://jayagrocer.com/sitemap.xml"]
    sitemap_rules = [
        (r"https://jayagrocer.com/products/[\w-]+", "parse_sd"),
    ]
