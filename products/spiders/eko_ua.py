import re
from scrapy.spiders import SitemapSpider
from products.structured_data_spider import StructuredDataSpider

class EkoUASpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for EKO Market (Ukraine) using zakaz.ua platform.

    Sample output:
    {
      "extras": {
        "@source_uri": "https://eko.zakaz.ua/uk/products/gel-dlia-prannia-losk--09000101800449/",
        "seller": {
          "@type": "Organization",
          "@id": "https://www.wikidata.org/wiki/Q12103350",
          "name": "EKO Market"
        }
      },
      "name": "Гель для прання Losk Color 1,485л",
      "website": "https://zakaz.ua/uk/products/gel-dlia-prannia-losk--09000101800449",
      "image": "https://img3.zakaz.ua/9e9418d06ea14d8297c6e90e777fdd31/1780030855-s350x350.jpg",
      "ref": "09000101800449",
      "sku": "09000101800449",
      "brand": "Losk",
      "offers": [
        {
          "@type": "Offer",
          "url": "https://eko.zakaz.ua/uk/products/gel-dlia-prannia-losk--09000101800449/",
          "priceCurrency": "UAH",
          "price": "352.00",
          "priceValidUntil": "",
          "availability": "https://schema.org/InStock",
          "seller": {
            "@type": "Organization",
            "name": "ЕКО Маркет"
          }
        }
      ],
      "price": "352.00",
      "proof_currency": "UAH",
      "located_in_wikidata": "Q12103350"
    }
    """
    name = "eko_ua"
    allowed_domains = ["zakaz.ua"]
    sitemap_urls = ["https://eko.zakaz.ua/sitemap.xml"]
    sitemap_rules = [
        (r"/products/.*--(\d+)", "parse_sd"),
    ]

    item_attributes = {
        "located_in_wikidata": "Q12103350",
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q12103350",
                "name": "EKO Market"
            }
        }
    }

    def post_process_item(self, item, response, ld_data):
        # Promote price and currency from offers if not already present
        if not item.get("price") or not item.get("proof_currency"):
            offers = ld_data.get("offers", [])
            if isinstance(offers, dict):
                offers = [offers]

            for offer in offers:
                if offer.get("price"):
                    item["price"] = offer["price"]
                if offer.get("priceCurrency"):
                    item["proof_currency"] = offer["priceCurrency"]
                break

        # Refine SKU and Brand
        sku = ld_data.get("sku")
        if not sku:
            # Try to get it from URL if missing in LD
            match = re.search(r"--(\d+)", response.url)
            if match:
                sku = match.group(1)

        if sku:
            if sku.startswith("ekomarket"):
                sku = sku.replace("ekomarket", "").lstrip("0")
            item["sku"] = sku
            item["ref"] = sku

        if brand := ld_data.get("brand"):
            if isinstance(brand, dict):
                item["brand"] = brand.get("name")
            else:
                item["brand"] = brand

        # Ensure located_in_wikidata is set
        item["located_in_wikidata"] = "Q12103350"

        yield item
