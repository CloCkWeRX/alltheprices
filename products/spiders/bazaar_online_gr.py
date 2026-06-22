from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

from products.structured_data_spider import StructuredDataSpider


class BazaarOnlineGRSpider(CrawlSpider, StructuredDataSpider):
    """
    Spider for Bazaar Supermarkets (Greece).
    Wikidata: Q4875086

    Sample output structured data:
    {
        "name": "Pils Hellas Κουτί 4x500ml",
        "website": "https://www.bazaar-online.gr/pils-hellas-500mlx4-mpyra-koyti",
        "description": "PILS HELLAS 500MLx4 ΜΠΥΡΑ ΚΟΥΤΙ",
        "image": "https://www.bazaar-online.gr/image/cache//catalog/product-upload/5201246002598_1-650x650.jpg",
        "ref": "5201246002598",
        "sku": "5201246002598",
        "brand": "PILS HELLAS",
        "offers": [
            {
                "@type": "Offer",
                "url": "https://www.bazaar-online.gr/pils-hellas-500mlx4-mpyra-koyti",
                "price": 3.69,
                "priceCurrency": "EUR",
                "availability": "https://schema.org/InStock"
            }
        ],
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q4875086",
                "name": "Bazaar"
            }
        }
    }
    """

    name = "bazaar_online_gr"
    allowed_domains = ["bazaar-online.gr"]
    start_urls = ["https://www.bazaar-online.gr/"]

    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q4875086",
                "name": "Bazaar",
            }
        }
    }

    rules = (
        Rule(
            LinkExtractor(
                deny=[
                    r"route=account/",
                    r"route=checkout/",
                    r"route=product/search",
                    r"compare-products",
                    r"search",
                    r"cart",
                    r"checkout",
                    r"login",
                    r"logout",
                    r"my-account",
                    r"vouchers",
                    r"wishlist",
                    r"order-history",
                    r"newsletter",
                    r"returns",
                    r"downloads",
                    r"transactions",
                    r"address-book",
                    r"reward-points",
                ]
            ),
            callback="parse_sd",
            follow=True,
        ),
    )

    def pre_process_data(self, ld_data: dict, **kwargs):
        if "model" in ld_data and "sku" not in ld_data:
            ld_data["sku"] = ld_data["model"]
