import re
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from products.items import Product


class TsuruyaJPSpider(CrawlSpider):
    """
    Spider for Tsuruya (Japan).
    Wikidata: Q11318832

    Sample output:
    {
        "name": "愛知県三河産やわらか新仔うなぎ蒲焼重【店舗受取・店舗支払い】",
        "website": "https://shop.tsuruya-corp.co.jp/products/detail/964",
        "ref": "964",
        "image": "https://shop.tsuruya-corp.co.jp/upload/save_image/0616094228_684f6874cc8f8.jpg",
        "offers": [
            {
                "@type": "Offer",
                "price": "2806",
                "priceCurrency": "JPY",
                "availability": "https://schema.org/InStock"
            }
        ],
        "proof_currency": "JPY",
        "located_in_wikidata": "Q11318832"
    }
    """

    name = "tsuruya_jp"
    allowed_domains = ["shop.tsuruya-corp.co.jp"]
    start_urls = ["https://shop.tsuruya-corp.co.jp/products/list"]

    rules = (
        Rule(LinkExtractor(allow=r"page=\d+")),
        Rule(LinkExtractor(allow=r"/products/detail/\d+"), callback="parse_item"),
    )

    def parse_item(self, response):
        product = Product()
        product["website"] = response.url

        name = response.css("h3.item_name::text").get()
        if name:
            product["name"] = name.strip()

        # Extract price - using tax-inclusive price (税込価格)
        price = response.xpath('//p[contains(@class, "sale_price") and contains(text(), "税込価格")]/span[@class="price01_default"]/text()').get()
        if not price:
            price = response.css("span.price01_default::text").get()

        if price:
            # Remove commas and other non-digit characters
            price = "".join(filter(str.isdigit, price))
            availability = "https://schema.org/InStock"
            if response.css("button.soldout"):
                availability = "https://schema.org/OutOfStock"

            product["offers"] = [
                {
                    "@type": "Offer",
                    "price": price,
                    "priceCurrency": "JPY",
                    "availability": availability,
                }
            ]

        image = response.css(".detail_img img::attr(src)").get()
        if image:
            product["image"] = response.urljoin(image)

        ref_match = re.search(r"/detail/(\d+)", response.url)
        if ref_match:
            product["ref"] = ref_match.group(1)

        product["proof_currency"] = "JPY"
        product["located_in_wikidata"] = "Q11318832"

        yield product
