import re
from scrapy.spiders import SitemapSpider
from products.items import Product
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST

class UniverexportRSSpider(SitemapSpider, StructuredDataSpider):
    """
    Univerexport (Serbia) spider.
    Fixes #255.
    Wikidata: Q12747294

    Sample output:
    {
        "name": "JABUKA AJDARED",
        "website": "https://elakolije.rs/1334599/proizvod/jabuka-ajdared",
        "image": "https://elakolije.rs/slike_pro/pro_v_1334599.jpg",
        "ref": "1334599",
        "located_in": "SRBIJA",
        "price": 149.99,
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q12747294",
                "name": "Univerexport"
            }
        }
    }
    """

    name = "univerexport_rs"
    allowed_domains = ["elakolije.rs"]
    sitemap_urls = ["https://elakolije.rs/out/sitemap.xml"]
    sitemap_rules = [(r"/(\d+)/proizvod/", "parse_product")]

    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q12747294",
                "name": "Univerexport",
            }
        }
    }

    custom_settings = {
        "USER_AGENT": FIREFOX_LATEST,
    }

    def parse_product(self, response):
        product = Product()
        product["website"] = response.url

        name = response.css("#proizvod_naslov::text").get()
        if name:
            product["name"] = name.strip()

        image = response.css("#proizvod_okvir_slika img::attr(src)").get()
        if image:
            product["image"] = response.urljoin(image)

        ref_match = re.search(r"/(\d+)/proizvod/", response.url)
        if ref_match:
            product["ref"] = ref_match.group(1)

        price = response.css("input.price::attr(value)").get()
        if price:
            try:
                product["price"] = float(price)
            except ValueError:
                pass

        brand = response.xpath("//th[contains(text(), 'Stavlja u promet')]/following-sibling::td/text()").get()
        if brand:
            product["brand"] = brand.replace("PROIZVODjAC:", "").strip()

        origin = response.xpath("//th[contains(text(), 'Zemlja porekla')]/following-sibling::td/text()").get()
        if origin:
            product["located_in"] = origin.strip()

        yield from self.post_process_item(product, response, {})
