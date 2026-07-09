import re
import chompjs
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from products.items import Product
from products.structured_data_spider import StructuredDataSpider

class SupertaiyoJPSpider(CrawlSpider, StructuredDataSpider):
    """
    Super Taiyo (Japan) spider.
    Fixes #389.
    Wikidata: Q11315814

    Sample output:
    {
        "name": "【ギフトお届け】★アサヒ「アサヒスーパードライ缶ビールセット」 ＡＳ-４Ｇ",
        "website": "https://www.shopping.super-taiyo.com/products/detail/8616",
        "image": "https://www.shopping.super-taiyo.com/upload/save_image/4902440125564_1.jpg",
        "ref": "8616",
        "gtin13": "4902440125564",
        "brand": "タイヨー",
        "brand_wikidata": "Q11315814",
        "description": "アサヒスーパードライ３５０ｍｌ缶×１０、アサヒスーパードライ５００ｍｌ缶×５",
        "price": 3350.0,
        "proof_currency": "JPY",
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q11315814",
                "name": "Taiyo"
            }
        }
    }
    """

    name = "supertaiyo_jp"
    allowed_domains = ["shopping.super-taiyo.com"]
    start_urls = ["https://www.shopping.super-taiyo.com/products/list"]

    rules = (
        Rule(LinkExtractor(allow=(r"/products/detail/\d+")), callback="parse_product"),
        Rule(LinkExtractor(allow=(r"/products/list\?pageno=\d+"))),
    )

    item_attributes = {
        "brand": "タイヨー",
        "brand_wikidata": "Q11315814",
        "proof_currency": "JPY",
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q11315814",
                "name": "Taiyo",
            }
        }
    }

    def parse_product(self, response):
        ref_match = re.search(r"/products/detail/(\d+)", response.url)
        if not ref_match:
            return

        product = Product()
        product["ref"] = ref_match.group(1)
        product["website"] = response.url

        # Extract data from JS object
        js_text = response.xpath("//script[contains(text(), 'productClassPriceList')]/text()").get()
        if js_text:
            data_match = re.search(r"var productClassPriceList = (\{.*?\});", js_text, re.DOTALL)
            if data_match:
                try:
                    data = chompjs.parse_js_object(data_match.group(1))
                    product_data = None
                    if product["ref"] in data:
                        product_data = data[product["ref"]]
                    else:
                        # Fallback to first key
                        product_data = next(iter(data.values()))

                    if product_data:
                        if "code" in product_data and product_data["code"]:
                            product["gtin13"] = product_data["code"]

                        if "price02" in product_data and "main_price1" in product_data["price02"]:
                            product["price"] = float(product_data["price02"]["main_price1"])
                except Exception:
                    pass

        name = response.css(".item_name::text").get()
        if not name:
            name = response.xpath("//meta[@property='og:title']/@content").get()
            if name:
                name = name.replace("タイヨーネット / ", "")
        if name:
            product["name"] = name.strip()

        image = response.css(".detail_img img::attr(src)").get()
        if image:
            product["image"] = response.urljoin(image)

        description = response.css("#detail_not_stock_box__description_detail::text").getall()
        if description:
            product["description"] = "\n".join([d.strip() for d in description if d.strip()])

        yield from self.post_process_item(product, response, {})
