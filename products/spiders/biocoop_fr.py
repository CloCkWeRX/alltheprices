from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from products.items import Product
from products.structured_data_spider import StructuredDataSpider


class BiocoopFRSpider(SitemapSpider, StructuredDataSpider):
    name = "biocoop_fr"
    allowed_domains = ["biocoop.fr"]
    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q2904039",
                "name": "Biocoop",
            }
        }
    }

    sitemap_urls = ["https://www.biocoop.fr/robots.txt"]
    sitemap_rules = [
        (r"https://www.biocoop.fr/[\w-]+.html", "parse_sd"),
    ]

    # TODO: If this pattern is common, extract to opengraphparser
    def post_process_item(self, item: Product, response: Response, ld_data: dict, **kwargs):

        price = response.xpath('//meta[@property="product:price:amount"]/@content').get()
        currency = response.xpath('//meta[@property="product:price:currency"]/@content').get()

        item["offers"] = {"@type": "Offer", "price": price, "priceCurrency": currency}

        yield item
