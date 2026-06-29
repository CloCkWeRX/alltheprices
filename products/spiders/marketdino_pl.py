from scrapy.spiders import SitemapSpider
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class MarketdinoPLSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Dino Polska (marketdino.pl).
    Extracts product data from Schema.org Product data in JSON-LD.
    Prices are extracted from HTML as they are missing in JSON-LD.

    Sample output:
    {
        "name": "Bombonierka Cherrissimo Mieszko 285g",
        "website": "https://marketdino.pl/produkt/bombonierka-cherrissimo-puszka-285g-mieszko",
        "ref": "bombonierka-cherrissimo-puszka-285g-mieszko",
        "image": "https://api.marketdino.pl/media/filer_public/8e/49/8e49c47e-3c2f-4783-b148-ea4ee5585b8a/bombonierka_cherrissimo_mieszko_285g.png",
        "offers": [
            {
                "@type": "Offer",
                "price": "21.85",
                "priceCurrency": "PLN",
                "availability": "https://schema.org/InStock"
            }
        ],
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q11694239",
                "name": "Dino Polska"
            }
        }
    }
    """

    name = "marketdino_pl"
    allowed_domains = ["marketdino.pl"]
    sitemap_urls = ["https://marketdino.pl/sitemap.xml"]
    sitemap_rules = [(r"/produkt/(.*)", "parse_sd")]

    custom_settings = {
        "USER_AGENT": FIREFOX_LATEST,
        "ROBOTSTXT_OBEY": False,
    }

    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q11694239",
                "name": "Dino Polska",
            }
        }
    }

    def post_process_item(self, item, response, ld_data):
        if not item.get("offers"):
            # Price is split into integer and decimal parts in the HTML
            # Example: <p class="... text-red ... font-impact ...">21 <span class="pennies ...">85</span></p>
            # Scoped to product details to avoid picking up related products
            price_container = response.xpath(
                '//div[contains(@class, "product-details")]//p[contains(@class, "text-red") and contains(@class, "font-impact")]'
            )
            if price_container:
                integer = price_container.xpath("text()").get()
                decimal = price_container.xpath('span[contains(@class, "pennies")]/text()').get()

                if integer and decimal:
                    price = f"{integer.strip()}.{decimal.strip()}".replace(" ", "")
                    item["offers"] = [
                        {
                            "@type": "Offer",
                            "price": price,
                            "priceCurrency": "PLN",
                            "availability": "https://schema.org/InStock",
                        }
                    ]
        yield item
