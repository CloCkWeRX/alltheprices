from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class AuchanPTSpider(SitemapSpider, StructuredDataSpider):
    name = "auchan_pt"
    allowed_domains = ["auchan.pt"]
    user_agent = FIREFOX_LATEST

    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q105857776",
                "name": "Auchan",
            }
        }
    }

    sitemap_urls = [
        "https://www.auchan.pt/sitemap_index.xml",
    ]
    sitemap_rules = [
        (r"/(\d+)\.html$", "parse"),
    ]
