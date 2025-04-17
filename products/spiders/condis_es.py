from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from products.items import Product
from products.structured_data_spider import StructuredDataSpider


class CondisESSpider(SitemapSpider, StructuredDataSpider):
    name = "condis_es"
    allowed_domains = ["condisline.com"]
    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q57417581",
                "name": "Condis",
            }
        }
    }

    sitemap_urls = ["https://condisline.com/robots.txt"]
    sitemap_rules = [
        (r"https://www.condisline.com/(.*).jsp", "parse_sd"),
    ]

    # TODO: If this pattern is common, extract to opengraphparser
    def post_process_item(self, item: Product, response: Response, ld_data: dict, **kwargs):

        price_js = response.xpath(
            '//script[contains(text(), "formatNumber(")]/text()'
        ).get()  # IE: formatNumber('1.29', 'list_price_111081');

        price = price_js.split("formatNumber('")[1].split("', ")[0]
        item["offers"][0]["price"] = price

        yield item
