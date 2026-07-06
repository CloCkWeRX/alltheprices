from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from products.structured_data_spider import StructuredDataSpider
from products.items import Product
from scrapy.http import Response


class LewiatanPLSpider(CrawlSpider, StructuredDataSpider):
    """
    Spider for Lewiatan (Poland).
    Wikidata: Q11755396

    Sample output:
    {
        "name": "Ryż basmati Ale dobre! 4x100 g",
        "website": "https://www.lewiatan.pl/produkty/przetwory-zbozowe-i-artykuly-sypkie/ryz-basmati-ale-dobre_4x100-g",
        "ref": "1138",
        "image": "https://www.lewiatan.pl/sites/default/files/styles/product_thumb/public/product/Ry%C5%BC%20basmati%204x100%20g.jpg?itok=LU4EFqrq",
        "offers": [
            {
                "@type": "Offer",
                "priceCurrency": "PLN",
                "availability": "https://schema.org/InStock"
            }
        ],
        "brand": "Lewiatan",
        "brand_wikidata": "Q11755396",
        "located_in_wikidata": "Q11755396",
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q11755396",
                "name": "Lewiatan"
            }
        }
    }
    """

    name = "lewiatan_pl"
    allowed_domains = ["lewiatan.pl"]
    start_urls = ["https://www.lewiatan.pl/produkty"]

    rules = (
        Rule(LinkExtractor(allow=r"/produkty/[^/]+$")),
        Rule(LinkExtractor(allow=r"/produkty/.*/.*_.*"), callback="parse_sd"),
    )

    item_attributes = {
        "brand": "Lewiatan",
        "brand_wikidata": "Q11755396",
        "located_in_wikidata": "Q11755396",
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q11755396",
                "name": "Lewiatan",
            }
        },
    }

    def iter_linked_data(self, response: Response):
        # Bespoke extraction as site lacks standard Schema.org JSON-LD
        name_parts = response.css("h1.product-details-header-title *::text").getall()
        name = " ".join([p.strip() for p in name_parts if p.strip()])

        if not name:
            return

        image = response.css(".product-details-image img::attr(src)").get()
        if image:
            image = response.urljoin(image)

        ref = response.css("a.product-details-basket-add::attr(data-basket-id)").get()
        if not ref:
            ref = response.url.split("/")[-1]

        yield {
            "@type": "Product",
            "name": name,
            "image": image,
            "sku": ref,
            "offers": {
                "@type": "Offer",
                "priceCurrency": "PLN",
                "availability": "https://schema.org/InStock",
            },
        }

    def post_process_item(self, item: Product, response: Response, ld_data: dict):
        if not item.get("ref"):
            item["ref"] = item.get("sku")
        yield item
