from products.structured_data_spider import StructuredDataSpider
from scrapy.spiders import SitemapSpider


class PicardFRSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Picard (France).
    Extracts product data from JSON-LD.

    Sample output:
    {
        "extras": {
            "@source_uri": "https://www.picard.fr/produits/filets-poulet-7-10-pieces-000000000000000545.html",
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q3382454",
                "name": "Picard Surgelés"
            }
        },
        "name": "Filets de poulet, 5 à 10 pièces",
        "website": "https://www.picard.fr/produits/filets-poulet-7-10-pieces-000000000000000545.html",
        "image": "https://www.picard.fr/dw/image/v2/AAHV_PRD/on/demandware.static/-/Sites-catalog-picard/default/dwdd0208dc/produits/000000000000000545_E.jpg?sw=672&sh=392&q=30",
        "ref": "000000000000000545",
        "offers": [
            {
                "@type": "Offer",
                "availability": "https://schema.org/InStock",
                "priceCurrency": "EUR",
                "priceValidUntil": "2026-06-28",
                "url": "https://www.picard.fr/produits/filets-poulet-7-10-pieces-000000000000000545.html",
                "price": "18.99"
            }
        ]
    }
    """

    name = "picard_fr"
    allowed_domains = ["picard.fr"]
    sitemap_urls = ["https://www.picard.fr/sitemap_0.xml"]
    sitemap_rules = [(r"/produits/.*-([A-Z0-9]+)\.html", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        if item.get("ref") == "null" or not item.get("ref"):
            item["ref"] = self.get_ref(response.url, response)

        yield item

    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q3382454",
                "name": "Picard Surgelés",
            }
        }
    }
