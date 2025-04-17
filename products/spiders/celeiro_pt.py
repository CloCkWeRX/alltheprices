from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class CeleiroPTSpider(SitemapSpider, StructuredDataSpider):
    name = "celeiro_pt"
    allowed_domains = ["celeiro.pt"]
    item_attributes = {
        "extras": {
            "seller": {"@type": "Organization", "@id": "https://www.wikidata.org/wiki/Q114102189", "name": "Celeiro"}
        }
    }

    sitemap_urls = ["https://celeiro.pt/robots.txt"]
    sitemap_rules = [
        (r"https://www.celeiro.pt/[\d]+-[\w-]+", "parse_sd"),
    ]
