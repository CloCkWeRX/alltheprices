from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from products.structured_data_spider import StructuredDataSpider

class WellcomeHKSpider(CrawlSpider, StructuredDataSpider):
    name = "wellcome_hk"
    allowed_domains = ["wellcome.com.hk"]
    start_urls = ["https://www.wellcome.com.hk/zh-hant/"]

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
        Rule(LinkExtractor(allow=r"/p/.+/i/.+\.html"), callback="parse_sd"),
        Rule(LinkExtractor(allow=r"/category/")),
    )

    item_attributes = {
        "extras": {
            "seller": {"@type": "Organization", "name": "Wellcome"}
        }
    }
