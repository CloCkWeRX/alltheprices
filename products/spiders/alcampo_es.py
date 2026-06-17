from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider
from products.user_agents import BROWSER_DEFAULT


class AlcampoESSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Alcampo (Spain).
    Wikidata: Q2832081

    Sample output structured data:
    {
        "@context": "https://schema.org",
        "@type": "Product",
        "sku": "50743",
        "name": "ESMIAGUA Agua mineral botella de 1,5 L, pack de 6 uds.",
        "description": "",
        "image": [
            "https://www.compraonline.alcampo.es/images-v3/37ea0506-72ec-4543-93c8-a77bb916ec12/c727f1db-21c1-4171-b011-3600149ad952/500x500.jpg",
            "https://www.compraonline.alcampo.es/images-v3/37ea0506-72ec-4543-93c8-a77bb916ec12/cbceb28e-214a-4ced-9dee-8b94488dd2c9/500x500.jpg"
        ],
        "brand": "ESMIAGUA",
        "size": "9000ml",
        "offers": {
            "@type": "Offer",
            "price": "1.80",
            "priceCurrency": "EUR",
            "itemCondition": "https://schema.org/NewCondition",
            "availability": "https://schema.org/InStock"
        }
    }
    """

    name = "alcampo_es"
    allowed_domains = ["compraonline.alcampo.es"]
    user_agent = BROWSER_DEFAULT

    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q2832081",
                "name": "Alcampo",
            }
        }
    }

    sitemap_urls = [
        "https://www.compraonline.alcampo.es/sitemaps/sitemap-products-part1.xml",
        "https://www.compraonline.alcampo.es/sitemaps/sitemap-products-part2.xml",
        "https://www.compraonline.alcampo.es/sitemaps/sitemap-products-part3.xml",
    ]
    sitemap_rules = [
        (r"/products/.*/(\d+)$", "parse"),
    ]
