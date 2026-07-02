import re
from scrapy.spiders import SitemapSpider
from products.items import Product
from products.structured_data_spider import StructuredDataSpider

class GyomusuperJPSpider(SitemapSpider, StructuredDataSpider):
    """
    Gyomu Super (Japan) spider.
    Fixes #320.
    Wikidata: Q105687460

    Sample output:
    {
        "name": "シリアルバー(ココナッツ＆チアシード)",
        "website": "https://www.gyomusuper.jp/product/detail.php?go_id=6077",
        "image": "https://www.gyomusuper.jp/onlineshop/html/upload/save_image/21460.png?1782955306",
        "ref": "6077",
        "gtin13": "5900749650977",
        "brand": "業務スーパー",
        "brand_wikidata": "Q105687460",
        "located_in": "ポーランド",
        "description": "ココナッツとスーパーフードのチアシード入りのシリアルバーです。オーツ麦や大麦などの穀物をベースに砂糖を使わず仕上げているので、素材の甘味や風味をお楽しみいただけます。",
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q105687460",
                "name": "Gyomu Super"
            }
        }
    }
    """

    name = "gyomusuper_jp"
    allowed_domains = ["gyomusuper.jp"]
    sitemap_urls = ["https://www.gyomusuper.jp/sitemap.xml"]
    sitemap_rules = [(r"detail\.php\?go_id=(\d+)", "parse_product")]

    item_attributes = {
        "brand": "業務スーパー",
        "brand_wikidata": "Q105687460",
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q105687460",
                "name": "Gyomu Super",
            }
        }
    }

    def parse_product(self, response):
        ref_match = re.search(r"go_id=(\d+)", response.url)
        if not ref_match:
            return

        product = Product()
        product["ref"] = ref_match.group(1)
        product["website"] = response.url

        name = response.css(".item_name::text").get()
        if not name:
            name = response.xpath("//meta[@property='og:title']/@content").get()
            if name:
                name = name.split(" - ")[0]
        if name:
            product["name"] = name.strip()

        image = response.css(".detail_img_box_slide img::attr(src)").get()
        if not image:
            image = response.xpath("//meta[@property='og:image']/@content").get()
        if image:
            product["image"] = response.urljoin(image)

        jan_text = response.css(".item_jan::text").get()
        if jan_text:
            jan_match = re.search(r"JANコード：(\d+)", jan_text)
            if jan_match:
                product["gtin13"] = jan_match.group(1)

        origin = response.xpath("//dl[dt[contains(text(), '原産国')]]/dd/text()").get()
        if origin:
            product["located_in"] = origin.strip()

        description = response.xpath("//meta[@name='description']/@content").get()
        if description:
            product["description"] = description.strip()

        yield from self.post_process_item(product, response, {})
