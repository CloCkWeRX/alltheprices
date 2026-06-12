from scrapy.spiders import Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider

from products.structured_data_spider import StructuredDataSpider


class WellcomeHKSpider(CrawlSpider, StructuredDataSpider):
    name = "wellcome_hk"
    allowed_domains = ["www.wellcome.com.hk"]
    start_urls = ["https://www.wellcome.com.hk/zh-hant/"]

    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q712534",
                "name": "Wellcome",
            }
        }
    }

    rules = (
        # Categories
        Rule(LinkExtractor(allow=(r"/zh-hant/wellcome/category/\d+/\d+\.html",))),
        # Products
        Rule(LinkExtractor(allow=(r"/zh-hant/wellcome/p/[^/]+/i/\d+\.html",)), callback="parse_sd"),
    )
