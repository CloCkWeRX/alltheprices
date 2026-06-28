from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class RukavychkaUASpider(SitemapSpider, StructuredDataSpider):
    name = "rukavychka_ua"
    allowed_domains = ["market.rukavychka.ua"]
    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q20092568",
                "name": "Rukavychka",
            }
        }
    }

    sitemap_urls = ["https://market.rukavychka.ua/sitemap-xml/"]
    sitemap_rules = [
        (r"https://market.rukavychka.ua/[^/]+-(\d+)$", "parse_sd"),
    ]

    @staticmethod
    def get_ref(url, response) -> str:
        return url.split("-")[-1]
