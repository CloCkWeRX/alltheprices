from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from products.items import Product
from products.structured_data_spider import StructuredDataSpider


class NabijiGESpider(SitemapSpider, StructuredDataSpider):
    name = "2nabiji_ge"
    allowed_domains = ["2nabiji.ge"]

    sitemap_urls = ["https://2nabiji.ge/robots.txt"]
    sitemap_rules = [
        (r"https://2nabiji.ge/ge/product/[\w-]+", "parse_sd"),
    ]

    # TODO: Post process item to get prices
    # TODO: If this pattern is common, extract to opengraphparser
    def post_process_item(self, item: Product, response: Response, ld_data: dict, **kwargs):

        # ,"price":10.95,"discountPrice":0
        price_js = response.xpath("//script[contains(text(), '\"discountPrice\":')]/text()").get(0)
        price = price_js.split('"price":')[1].split(",")[0]

        item["offers"][0]["price"] = price

        yield item
