from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class ShopmetroPHSpider(SitemapSpider, StructuredDataSpider):
    """
    ShopMetro (Philippines) spider.
    Retailer: Metro Retail Stores Group, Inc. (Q23808789)
    """

    name = "shopmetro_ph"
    allowed_domains = ["shopmetro.ph"]

    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q23808789",
                "name": "The Metro Stores",
            }
        }
    }

    sitemap_urls = ["https://shopmetro.ph/sitemap_index.xml"]
    sitemap_rules = [
        (r"/product/", "parse_sd"),
    ]
