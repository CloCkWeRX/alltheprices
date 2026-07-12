from scrapy.spiders import SitemapSpider
from products.structured_data_spider import StructuredDataSpider

class UnimarcCLSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Unimarc (Chile) (Q6156244).
    Fixes #170.

    Sample output:
    {
      "name": "palta hass malla 1 kg",
      "website": "https://www.unimarc.cl/product/palta-hass-malla-1-kg",
      "image": "https://unimarc.vtexassets.com/arquivos/ids/162200/Palta-Hass-malla-1-Kg.jpg?v=636486731472500000",
      "ref": "palta-hass-malla-1-kg",
      "sku": "280",
      "brand": "Frutas Y Verduras",
      "offers": [
        {
          "@type": "Offer",
          "url": "https://www.unimarc.cl/product/palta-hass-malla-1-kg",
          "priceCurrency": "CLP",
          "price": "3590",
          "availability": "https://schema.org/inStock"
        }
      ],
      "price": "3590",
      "proof_currency": "CLP",
      "located_in_wikidata": "Q6156244"
    }
    """
    name = "unimarc_cl"
    allowed_domains = ["unimarc.cl"]
    sitemap_urls = ["https://www.unimarc.cl/sitemap.xml"]
    sitemap_rules = [
        (r"/product/([^/]+)$", "parse_sd"),
    ]

    custom_settings = {
        "USER_AGENT": "Googlebot/2.1 (+http://www.google.com/bot.html)",
    }

    def post_process_item(self, item, response, ld_data):
        item["located_in_wikidata"] = "Q6156244"

        if not item.get("price") or not item.get("proof_currency"):
            offers = ld_data.get("offers", [])
            if isinstance(offers, dict):
                offers = [offers]

            for offer in offers:
                if offer.get("price") and not item.get("price"):
                    item["price"] = offer["price"]
                if offer.get("priceCurrency") and not item.get("proof_currency"):
                    item["proof_currency"] = offer["priceCurrency"]

                if item.get("price") and item.get("proof_currency"):
                    break

        yield item
