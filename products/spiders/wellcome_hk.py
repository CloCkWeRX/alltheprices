from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from products.structured_data_spider import StructuredDataSpider


class WellcomeHKSpider(CrawlSpider, StructuredDataSpider):
    name = "wellcome_hk"
    allowed_domains = ["wellcome.com.hk"]
    start_urls = ["https://www.wellcome.com.hk/en/wellcome/category/100011/1.html"]

    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q706247",
                "name": "Wellcome",
            }
        }
    }

    rules = (
        Rule(LinkExtractor(allow=r"/en/wellcome/category/\d+/\d+\.html")),
        Rule(LinkExtractor(allow=r"/en/wellcome/p/[^/]+/i/\d+\.html"), callback="parse_sd"),
    )
