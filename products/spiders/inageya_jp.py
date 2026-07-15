import re
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from products.items import Product
from products.structured_data_spider import StructuredDataSpider


class InageyaJPSpider(CrawlSpider, StructuredDataSpider):
    """
    Inageya (Japan) spider.
    Fixes #8.
    Wikidata: Q17193392

    Sample output:
    {
        "name": "【エントリーでP5倍】 お中元 夏ギフト スイーツ アイスクリーム 食べ比べ ハーゲンダッツ ミニカップ12個セット 御中元 中元 2026 送料無料 夏 贈答用 詰め合わせ お取り寄せ 中元ギフト 人気 高級 上司 友人 親戚 家族 両親 同僚 内祝い お祝い 御祝 お礼 御礼",
        "website": "https://item.rakuten.co.jp/inageya320/32131/",
        "image": "https://tshop.r10s.jp/inageya320/cabinet/26summer_inageya/26summer_p5/32131_p5.jpg",
        "ref": "32131",
        "brand": "いなげや",
        "brand_wikidata": "Q17193392",
        "price": 4880.0,
        "proof_currency": "JPY",
        "offers": [
            {
                "@type": "Offer",
                "price": 4880,
                "priceCurrency": "JPY",
                "availability": "http://schema.org/InStock"
            }
        ],
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q17193392",
                "name": "いなげや"
            }
        }
    }
    """

    name = "inageya_jp"
    allowed_domains = ["item.rakuten.co.jp"]
    start_urls = ["https://item.rakuten.co.jp/inageya320/c/0000005438/"]

    rules = (
        Rule(LinkExtractor(allow=(r"/inageya320/[a-zA-Z0-9_-]+/$")), callback="parse_sd"),
        Rule(LinkExtractor(allow=(r"/inageya320/c/\d+/"))),
    )

    item_attributes = {
        "brand": "いなげや",
        "brand_wikidata": "Q17193392",
        "proof_currency": "JPY",
        "located_in_wikidata": "Q1490",  # Tokyo, Japan
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q17193392",
                "name": "いなげや",
            }
        }
    }

    def post_process_item(self, item: Product, response, ld_data, **kwargs):
        # StructuredDataSpider extracts price from Offers.
        if "offers" in item and item["offers"]:
            offer = item["offers"][0] if isinstance(item["offers"], list) else item["offers"]
            if "price" in offer:
                item["price"] = float(offer["price"])
            if "priceCurrency" in offer:
                item["proof_currency"] = offer["priceCurrency"]

        # Ensure we have a clean ref
        ref_match = re.search(r"/inageya320/([a-zA-Z0-9_-]+)/", response.url)
        if ref_match:
            item["ref"] = ref_match.group(1)

        # Merge item_attributes
        for key, val in self.item_attributes.items():
            if key == "extras":
                item["extras"] = {**item.get("extras", {}), **val}
            else:
                item[key] = val

        yield item
