from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from products.structured_data_spider import StructuredDataSpider

class MarketplaceHKSpider(CrawlSpider, StructuredDataSpider):
    name = "marketplace_hk"
    allowed_domains = ["marketplacehk.com"]
    start_urls = ["https://www.marketplacehk.com/zh-hant"]

    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q6770713",
                "name": "Market Place",
            }
        }
    }

    rules = (
        Rule(LinkExtractor(allow=r"/p/.+/i/.+\.html"), callback="parse_sd"),
        Rule(LinkExtractor(allow=r"/category/")),
    )
