import re
import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from products.items import Product
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class InageyaJPSpider(CrawlSpider, StructuredDataSpider):
    """
    Inageya (Japan) spider.
    https://inageya-shop.com/

    Wikidata: Q17193392
    Fixes #8.

    Sample output:
    {
        "name": "まねき食品 まねきの冷凍えきそば6食セット 離島不可 （54348）",
        "website": "https://inageya-shop.com/item/1195-4931",
        "image": "https://inageya-shop.com/item/thumb/5/54348.jpg",
        "ref": "1195-4931",
        "brand": "いなげや",
        "price": 3564.0,
        "proof_currency": "JPY",
        "located_in_wikidata": "Q17193392",
        "offers": [
            {
                "@type": "Offer",
                "price": "3564.0",
                "priceCurrency": "JPY",
                "availability": "https://schema.org/InStock"
            }
        ]
    }
    """

    name = "inageya_jp"
    allowed_domains = ["inageya-shop.com"]
    start_urls = [
        "https://inageya-shop.com/list/22frozen01",
    ]

    custom_settings = {
        "USER_AGENT": FIREFOX_LATEST,
        "ROBOTSTXT_OBEY": False,
    }

    rules = (
        # Product pages
        Rule(LinkExtractor(allow=r"/item/\d+-\d+$"), callback="parse_product"),
        # Category / list pages
        Rule(LinkExtractor(allow=r"/list/[a-zA-Z0-9_-]+$")),
    )

    item_attributes = {
        "brand": "いなげや",
        "brand_wikidata": "Q17193392",
        "proof_currency": "JPY",
        "located_in_wikidata": "Q17193392",
    }

    def parse_product(self, response):
        product = Product()
        product["website"] = response.url

        # Extract name
        name = response.css("span.item-name::text").get()
        if not name:
            name = response.css("span.page-name::text").get()
        if name:
            product["name"] = name.strip()

        # Extract image
        image = response.css("img.uri-to-img.size-lg::attr(src)").get()
        if not image:
            image = response.css("img.uri-to-img::attr(src)").get()
        if image:
            product["image"] = response.urljoin(image)

        # Extract reference / item code
        ref = None
        match = re.search(r"/item/(\d+-\d+)", response.url)
        if match:
            ref = match.group(1)
        if not ref:
            ref = response.css("span.item-code span.value::text").get()
        if ref:
            product["ref"] = ref

        if ref:
            pricing_url = f"https://inageya-shop.com/ps/item_purchase.jsp?ar={ref}&ofr=&size=regular"
            yield scrapy.Request(
                url=pricing_url,
                callback=self.parse_price,
                meta={"product": product},
            )
        else:
            yield from self.post_process_item(product, response, {})

    def parse_price(self, response):
        product = response.meta["product"]
        all_text = " ".join([t.strip() for t in response.xpath("//text()").getall() if t.strip()])
        match = re.search(r"([\d,]+)\s*円", all_text)
        if match:
            price_str = match.group(1).replace(",", "")
            product["price"] = float(price_str)

        if product.get("price"):
            availability = "https://schema.org/InStock" if "在庫があります" in all_text else "https://schema.org/OutOfStock"
            product["offers"] = [{
                "@type": "Offer",
                "price": str(product["price"]),
                "priceCurrency": "JPY",
                "availability": availability,
            }]

        yield from self.post_process_item(product, response, {})
