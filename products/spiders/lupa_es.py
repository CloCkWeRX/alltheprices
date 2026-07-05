from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class LupaESSpider(SitemapSpider, StructuredDataSpider):
    """
    Scraper for Lupa (Spain).
    https://www.lupaonline.com/

    Sample output:
    {
        "name": "Aceite Abril Oliva Intenso Litro",
        "website": "https://www.lupaonline.com/santander/aceite-abril-oliva-intenso-lt-102108",
        "image": "https://www.lupaonline.com/media/catalog/product/cache/0b22c8a128ee9aeccd1570def5c6617a/1/0/102108_2.jpg",
        "ref": "102108",
        "sku": "102108",
        "offers": [
            {
                "@type": "Offer",
                "url": "https://www.lupaonline.com/santander/aceite-abril-oliva-intenso-lt-102108",
                "priceCurrency": "EUR",
                "price": "3.95",
                "availability": "https://schema.org/InStock",
                "itemCondition": "https://schema.org/NewCondition",
                "seller": {"@id": "https://www.lupaonline.com/santander/#organization"}
            }
        ],
        "proof_currency": "EUR",
        "price": 3.95,
        "located_in_wikidata": "Q12267744"
    }
    """

    name = "lupa_es"
    allowed_domains = ["lupaonline.com"]
    sitemap_urls = ["https://www.lupaonline.com/media/sitemap/sitemap_santande.xml"]
    sitemap_rules = [
        (r"-(\d+)$", "parse_sd"),
    ]

    custom_settings = {
        "USER_AGENT": FIREFOX_LATEST,
        "ROBOTSTXT_OBEY": False,
    }

    item_attributes = {
        "proof_currency": "EUR",
        "located_in_wikidata": "Q12267744",
    }

    def post_process_item(self, item, response, ld_data):
        if item.get("offers"):
            price = item["offers"][0].get("price")
            if price:
                item["price"] = float(price)
        yield item
