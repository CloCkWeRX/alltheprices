from scrapy.http import Response
from scrapy.spiders import SitemapSpider

# from products.categories import PaymentMethods, map_payment
from products.items import Product
from products.structured_data_spider import StructuredDataSpider


class OdinNLSpider(SitemapSpider, StructuredDataSpider):
    name = "odin_nl"
    allowed_domains = ["odin.nl"]
    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q114839627",
                "name": "Coöperatie Odin",
            }
        }
    }

    sitemap_urls = ["https://www.odin.nl/robots.txt"]
    sitemap_rules = [
        # https://www.odin.nl/producten/alle-producten/-185916-pikante-kip-salade/
        (r"https://www.odin.nl/producten/alle-producten/[\w-]+/", "parse_sd"),
    ]

    def map_properties(self, item: Product, response: Response):
        article_properties = response.xpath('//div[@class="article-properties"]/div/dl/div')
        for article_property in article_properties:
            label = article_property.xpath("dt/text()").get()
            value = article_property.xpath("dd/text()").get().strip()

            if label == "EAN-code":
                item["gtin"] = value
            elif label == "Artikelcode":
                item["ref"] = value
            elif label == "Kiloprijs":
                item["extras"]["price_kg"] = value
            elif label == "Kwaliteit":
                # BIO? Any others?
                if value == "-":
                    pass
                else:  # BIO, any other labels?
                    item["extras"]["quality"] = value
            elif label == "Land van herkomst":
                item["extras"]["countryOfOrigin"] = value
            else:
                item["extras"][label] = value

    def map_prices(self, item: Product, response: Response):
        item["offers"] = []
        article_properties = response.xpath('//div[@class="article-info"]/dl/div')
        for article_property in article_properties:
            label = article_property.xpath("dt/text()").get().strip()
            value = article_property.xpath("dd/span/text()").get().strip()

            if label == "Merk":
                item["brand"] = value
            elif label == "Inhoud":
                # Weight
                # 250 GR
                pass
            elif label == "Prijs":
                # Price
                # € 4,59
                item["offers"].append({"price": value.split("€ ")[1].replace(",", "."), "priceCurrency": "EUR"})
            elif label == "Ledenprijs":
                # Member Price
                # € 3,89
                item["offers"].append(
                    {"name": "Ledenprijs", "price": value.split("€ ")[1].replace(",", "."), "priceCurrency": "EUR"}
                )
            else:
                print(label)
                print(value)

    def post_process_item(self, item: Product, response: Response, ld_data: dict, **kwargs):
        """Override with any post-processing on the item."""
        self.map_properties(item, response)
        self.map_prices(item, response)

        yield item
