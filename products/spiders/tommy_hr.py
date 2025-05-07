from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class TommyHRSpider(SitemapSpider, StructuredDataSpider):
    name = "tommy_hr"
    allowed_domains = ["tommy.hr"]
    item_attributes = {
        "extras": {
            "seller": {"@type": "Organization", "@id": "https://www.wikidata.org/wiki/Q12643718", "name": "Tommy"}
        }
    }

    sitemap_urls = ["https://www.tommy.hr/sitemap.xml"]
    sitemap_rules = [
        (r"https://www.tommy.hr/proizvodi/[\w-]+", "parse_sd"),
    ]

    # TODO: 'https://www.tommy.hr/assets/no-image.png should be dropped
