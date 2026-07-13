import re
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from products.items import Product
from products.structured_data_spider import StructuredDataSpider


class TokyuStoreJPSpider(CrawlSpider, StructuredDataSpider):
    """
    Tokyu Store (Japan) spider.
    Fixes #9.
    Wikidata: Q11526963

    Sample output:
    {
        "name": "Vマーク ポテトチップス のり塩味   130g",
        "website": "https://ns.tokyu-bell.jp/shop/g/g16810051/",
        "image": "https://ns.tokyu-bell.jp/img/goods/S/4949486702847.jpg",
        "ref": "16810051",
        "brand": "東急ストア",
        "brand_wikidata": "Q11526963",
        "price": 235.0,
        "proof_currency": "JPY",
        "offers": [
            {
                "@type": "Offer",
                "price": 235,
                "priceCurrency": "JPY",
                "availability": "http://schema.org/InStock"
            }
        ],
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q11526963",
                "name": "Tokyu Store"
            }
        }
    }
    """

    name = "tokyu_store_jp"
    allowed_domains = ["ns.tokyu-bell.jp"]
    start_urls = ["https://ns.tokyu-bell.jp/shop/c/cC10"]

    rules = (
        Rule(LinkExtractor(allow=(r"/shop/g/g(\d+)/")), callback="parse_sd"),
        Rule(LinkExtractor(allow=(r"/shop/c/c\w+/"))),
    )

    item_attributes = {
        "brand": "東急ストア",
        "brand_wikidata": "Q11526963",
        "proof_currency": "JPY",
        "located_in_wikidata": "Q1490",  # Tokyo, Japan
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q11526963",
                "name": "Tokyu Store",
            }
        }
    }

    def post_process_item(self, item: Product, response, ld_data, **kwargs):
        # StructuredDataSpider extracts price from Offers.
        # But let's make sure 'price' and 'proof_currency' are set properly if offers is present.
        if "offers" in item and item["offers"]:
            offer = item["offers"][0] if isinstance(item["offers"], list) else item["offers"]
            if "price" in offer:
                item["price"] = float(offer["price"])
            if "priceCurrency" in offer:
                item["proof_currency"] = offer["priceCurrency"]

        # Ensure we have a clean ref
        ref_match = re.search(r"/shop/g/g(\d+)/", response.url)
        if ref_match:
            item["ref"] = ref_match.group(1)

        # Merge item_attributes
        for key, val in self.item_attributes.items():
            if key == "extras":
                item["extras"] = {**item.get("extras", {}), **val}
            else:
                item[key] = val

        yield item
