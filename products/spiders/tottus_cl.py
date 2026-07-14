from scrapy.spiders import SitemapSpider
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST

class TottusCLSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Tottus (Chile) (Q11005230).
    Fix #169.

    Sample output:
    {
        "name": "Bolsa de Basura Superior Chica 50 x 65 cms",
        "website": "https://www.tottus.cl/tottus-cl/articulo/110615128/Bolsa-de-Basura-Superior-Chica-50-x-65-cms/110615129",
        "image": "https://media.falabella.com/tottusCL/20386259_1/public",
        "ref": "110615129",
        "sku": "110615129",
        "brand": "SUPERIOR",
        "offers": [
            {
                "@type": "Offer",
                "priceCurrency": "CLP",
                "price": "520",
                "availability": "https://schema.org/InStock",
                "sku": "110615129",
                "seller": {
                    "@type": "Organization",
                    "name": "Tottus"
                }
            }
        ],
        "price": 520,
        "proof_currency": "CLP",
        "located_in_wikidata": "Q11005230"
    }
    """
    name = "tottus_cl"
    allowed_domains = ["tottus.cl"]
    sitemap_urls = ["https://www.tottus.cl/static/site/sitemaps/pdp/pdp_cl_TO_COM-index.xml"]
    sitemap_rules = [
        (r"/articulo/[^/]+/.*?/([^/]+)$", "parse_sd"),
    ]

    custom_settings = {
        "USER_AGENT": FIREFOX_LATEST,
        "ROBOTSTXT_OBEY": False,
    }

    def post_process_item(self, item, response, ld_data):
        item["located_in_wikidata"] = "Q11005230"

        # Tottus CLP prices might be string numbers like "520"
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

        if item.get("price") is not None:
            try:
                item["price"] = float(str(item["price"]).replace(",", ".").strip())
            except ValueError:
                pass

        yield item
