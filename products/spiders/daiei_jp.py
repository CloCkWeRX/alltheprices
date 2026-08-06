import re
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

from products.items import Product
from products.user_agents import FIREFOX_LATEST


class DaieiJPSpider(CrawlSpider):
    """
    Spider for Daiei (Japan).
    Wikidata: Q3543891
    Fix #438 or Fix #483.

    Sample output:
    {
        "name": "ハーゲンダッツ バラエティセット（010016）",
        "website": "https://gift.daiei.co.jp/shopping/ochugen2026/products-detail/7967",
        "image": "https://gift.daiei.co.jp/assets/img/products/4976994426057/4976994426057-1.jpg",
        "ref": "7967",
        "sku": "7967",
        "gtin": "4976994426057",
        "brand": "ハーゲンダッツ",
        "located_in_wikidata": "Q3543891",
        "price": 5400.0,
        "proof_currency": "JPY"
    }
    """

    name = "daiei_jp"
    allowed_domains = ["gift.daiei.co.jp"]
    start_urls = ["https://gift.daiei.co.jp/sitemap", "https://gift.daiei.co.jp/"]

    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": FIREFOX_LATEST,
    }

    rules = (
        # Follow campaign pages (e.g. /shopping/ochugen2026)
        Rule(LinkExtractor(allow=r"/shopping/[\w_-]+$")),
        # Follow campaign index pages
        Rule(LinkExtractor(allow=r"/shopping/[\w_-]+/index/\d+")),
        # Parse product detail pages
        Rule(
            LinkExtractor(allow=r"/shopping/[\w_-]+/products-detail/\d+"),
            callback="parse_product",
        ),
    )

    def parse_product(self, response):
        name = response.css("h1.product-detail__ttl::text").get()
        if name:
            name = name.strip()

        # Parse reference ID from URL
        ref_match = re.search(r"/products-detail/(\d+)", response.url)
        ref = ref_match.group(1) if ref_match else None

        # Parse price (tax excluded preferred, fall back to tax included)
        price_taxout = response.css(".product-detail__price__taxout strong::text").get()
        price = None
        if price_taxout:
            try:
                price = float(price_taxout.replace(",", "").strip())
            except ValueError:
                pass

        if price is None:
            price_taxin = response.css(".product-detail__price__taxin::text").get()
            if price_taxin:
                m = re.search(r"税込\s*([\d,]+)円", price_taxin)
                if m:
                    try:
                        price = float(m.group(1).replace(",", "").strip())
                    except ValueError:
                        pass

        # Image extraction
        image = response.css(".product-detail__thumb img::attr(src)").get()
        if not image:
            image = response.css(".product-detail__left-content img::attr(src)").get()
        if image:
            image = response.urljoin(image)

        # GTIN/JAN code extraction from the image path
        gtin = None
        if image:
            gtin_match = re.search(r"/products/(\d{13})/", image)
            if gtin_match:
                gtin = gtin_match.group(1)

        # Brand extraction (first word in the title)
        brand = None
        if name:
            parts = re.split(r"[\s\u3000]+", name)
            if parts:
                brand = parts[0]

        product = Product(
            name=name,
            website=response.url,
            ref=ref,
            sku=ref,
            image=image,
            brand=brand,
            located_in_wikidata="Q3543891",
            price=price,
            proof_currency="JPY",
        )

        if gtin:
            product["gtin"] = gtin
            product["gtin13"] = gtin

        product["extras"] = {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q3543891",
                "name": "Daiei",
            }
        }

        yield product
