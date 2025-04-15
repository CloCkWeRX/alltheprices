from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class MpriesATSpider(SitemapSpider, StructuredDataSpider):
    name = "mpreis_at"
    allowed_domains = ["mpreis.at"]
    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q873491",
                "name": "Mpries",
            }
        }
    }

    sitemap_urls = ["https://www.mpreis.at/robots.txt"]
    sitemap_rules = [
        (r"https://www.mpreis.at/shop/p/[\w-]+", "parse_sd"),
    ]
