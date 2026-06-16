from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class EatalyComSpider(SitemapSpider, StructuredDataSpider):
    name = "eataly_com"
    allowed_domains = ["eataly.com"]
    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q3046645",
                "name": "Eataly",
            }
        }
    }

    sitemap_urls = ["https://www.eataly.com/robots.txt"]
    sitemap_rules = [
        (r"https://www.eataly.com/us_en/[^/]+$", "parse_sd"),
        (r"https://www.eataly.com/[^/]+$", "parse_sd"),
    ]

    custom_settings = {
        "CLOSESPIDER_TIMEOUT": 120,
    }
