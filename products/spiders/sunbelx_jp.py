import re
from products.items import Product
from products.structured_data_spider import StructuredDataSpider

class SunbelxJPSpider(StructuredDataSpider):
    """
    Sun Bel'x (Japan) spider.
    Fixes #332.
    Wikidata: Q11305967

    Sample output:
    {
        "name": "【直輸入】南フランス産ワイン　各種",
        "website": "https://sunbelx.com/product/304",
        "image": "https://sunbelx.com/upload/Product/images/img_304_68940cf0-69f4-4beb-a2cd-4a26b7b55302.png",
        "ref": "304",
        "brand": "スーパーベルクス",
        "brand_wikidata": "Q11305967",
        "description": "南フランス産ワイン3種類。それぞれ特徴がありますが、すべて飲みやすく果実味が強いです。金賞受賞ワインなので品質は折り紙付き。食卓や気分に合わせてお選びください。普段の家飲みがリッチに、贅沢になります。ジュー・ド・ロワ・カベルネ＆シラーIGP…カベルネ50％、シラー50％。アメリカの超有名スーパー・Trader Joe'sでも大人気！果実味・コク・飲みやすさ◎。フランスオーク樽で5か月熟成。こんなワイン毎日飲めたら幸せです♡\nロッシュ・ド・ベラーヌ・コロンバール…2024年金賞受賞白ワイン。酸味とコクが特徴です。香りはグレープフルーツ、味は青りんご。生ハム・前菜と相性◎。\nラ・フール・カベルネソーヴィニヨン…2024年金賞受賞赤ワイン。コク・果実味がすごい。アメリカの超有名スーパー・Trader Joe'sでも販売。フルボディだけど渋み控えめ。ピザ・ローストビーフと相性◎。",
        "price": 777.0,
        "proof_currency": "JPY",
        "date": "2025-04-04",
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q11305967",
                "name": "Sun Bel'x"
            }
        }
    }
    """

    name = "sunbelx_jp"
    allowed_domains = ["sunbelx.com"]
    start_urls = [
        "https://sunbelx.com/product/",
        "https://sunbelx.com/product/304",
    ]

    item_attributes = {
        "brand": "スーパーベルクス",
        "brand_wikidata": "Q11305967",
        "proof_currency": "JPY",
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q11305967",
                "name": "Sun Bel'x",
            }
        }
    }

    def parse(self, response):
        if "/product/" in response.url and response.url.split("/")[-1].isdigit():
            yield from self.parse_product(response)
            return

        # Product links
        for link in response.css("a::attr(href)").getall():
            if re.search(r"/product/(\d+)$", link):
                yield response.follow(link, self.parse_product)

        # Pagination
        for next_page in response.css(".next a::attr(href)").getall():
            yield response.follow(next_page, self.parse)

    def parse_product(self, response):
        ref_match = re.search(r"/product/(\d+)$", response.url)
        if not ref_match:
            return

        product = Product()
        product["ref"] = ref_match.group(1)
        product["website"] = response.url

        name = response.css(".product_detail__info__title::text").get()
        if not name:
            name = response.xpath("//meta[@property='og:title']/@content").get()
            if name:
                name = name.split("｜")[0]
        if name:
            product["name"] = name.strip()

        image = response.css(".product_detail__info figure img::attr(src)").get()
        if not image:
            image = response.xpath("//meta[@property='og:image']/@content").get()
        if image:
            product["image"] = response.urljoin(image)

        price_text = response.css(".product_detail__info__des::text").get()
        if price_text:
            price_match = re.search(r"(\d+)円", price_text)
            if price_match:
                product["price"] = float(price_match.group(1))

        description_paras = response.css(".product_detail__para p::text").getall()
        if description_paras:
            product["description"] = "\n".join([p.strip() for p in description_paras if p.strip()])

        date = response.css(".product_detail__info__time::attr(datetime)").get()
        if date:
            product["date"] = date.strip()

        yield from self.post_process_item(product, response, {})
