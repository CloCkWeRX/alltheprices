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
            label_node = article_property.xpath("dt/text()").get()
            value_node = article_property.xpath("dd/text()").get()

            label = label_node.strip() if label_node else None
            value = value_node.strip() if value_node else ""

            if not label:
                continue

            if label == "EAN-code":
                item["gtin"] = value
            elif label == "Artikelcode":
                item["ref"] = value
            elif label == "Kiloprijs" or label == "Literprijs":
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
            label_node = article_property.xpath("dt/text()").get()
            if not label_node:
                continue
            label = label_node.strip()

            value_node = article_property.xpath("dd/span/text()").get() or article_property.xpath("dd/text()").get()
            if not value_node:
                value_node = "".join(article_property.xpath("dd//text()").getall()).strip()

            if not value_node:
                continue
            value = value_node.strip()

            if label == "Merk":
                item["brand"] = value
            elif label == "Inhoud":
                # Weight
                # 250 GR
                pass
            elif label == "Prijs":
                # Price
                # € 4,59
                if "€ " in value:
                    item["offers"].append({"price": value.split("€ ")[1].replace(",", "."), "priceCurrency": "EUR"})
            elif label == "Ledenprijs":
                # Member Price
                # € 3,89
                if "€ " in value:
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

        # Extract product description from div.product-description
        description = "".join(response.xpath('//div[@class="product-description"]//text()').getall()).strip()
        if description:
            item["description"] = description

        # Extract sections from div.product-info
        product_info_div = response.xpath('//div[@class="product-info"]')
        if product_info_div:
            h2_headers = product_info_div.xpath('.//h2')
            for h2 in h2_headers:
                header_text = h2.xpath('text()').get()
                if not header_text:
                    continue
                header_text = header_text.strip().lower()

                # Get the following sibling text node
                sibling_text = h2.xpath('following-sibling::text()[1]').get()
                if sibling_text and sibling_text.strip():
                    sibling_text = sibling_text.strip()
                else:
                    # Sibling could be in a p tag or span tag
                    sibling_text = "".join(h2.xpath('following-sibling::*[1]//text()').getall()).strip()

                if sibling_text:
                    if "ingredi" in header_text:
                        item["extras"]["ingredients"] = sibling_text
                    elif "gebruiker" in header_text or "tips" in header_text:
                        item["extras"]["usage"] = sibling_text
                    elif "suggestie" in header_text:
                        item["extras"]["suggestions"] = sibling_text
                    elif "voeding" in header_text:
                        item["extras"]["nutrients"] = sibling_text

        yield item
