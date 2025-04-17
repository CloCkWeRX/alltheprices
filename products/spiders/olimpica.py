from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class OlimpicaSpider(SitemapSpider, StructuredDataSpider):
    name = "olimpica"
    allowed_domains = ["olimpica.com"]
    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q24749847",
                "name": "Olímpica",
            }
        }
    }

    sitemap_urls = ["https://www.olimpica.com/robots.txt"]
    sitemap_rules = [
        (r"https://www.olimpica.com/[\w-]+/p", "parse_sd"),
    ]
