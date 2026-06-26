from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from products.items import Product
from products.structured_data_spider import StructuredDataSpider


class SvetoforRUSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Svetofor (svetoforonline.ru).
    Russian discount supermarket chain.

    Sample output:
    {
        "extras": {
            "@source_uri": "https://svetoforonline.ru/bakaleya-i-drugie-produkti/bakaleya/krupi/krupa-pshenichnaya-poltavskaya-no2-0,7kg-uvelka.htm",
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q61875920",
                "name": "Svetofor"
            }
        },
        "name": "Крупа пшеничная Полтавская №2 0,7кг Увелка",
        "website": "https://svetoforonline.ru/bakaleya-i-drugie-produkti/bakaleya/krupi/krupa-pshenichnaya-poltavskaya-no2-0,7kg-uvelka.htm",
        "ref": "0121198",
        "image": "https://svetoforonline.ru/data/share/item_984_big.jpg",
        "offers": [
            {
                "@type": "Offer",
                "price": "45.90",
                "priceCurrency": "RUB",
                "availability": "https://schema.org/InStock"
            }
        ]
    }
    """

    name = "svetofor_ru"
    allowed_domains = ["svetoforonline.ru"]
    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q61875920",
                "name": "Svetofor",
            }
        }
    }

    sitemap_urls = ["https://svetoforonline.ru/sitemap.xml"]
    sitemap_rules = [
        (r"\.html?$", "parse_sd"),
        (r"/[^/]+/[^/]+/[^/]+/$", "parse_sd"),
    ]

    wanted_types = ["Product", "IndividualProduct"]

    def post_process_item(self, item: Product, response: Response, ld_data: dict, **kwargs):
        """Manual extraction as fallback or to complement microdata."""

        # Extract name if missing or better available
        name = response.xpath('//span[@itemtype="http://schema.org/Product"]//span[@itemprop="name"]/text()').get()
        if not name:
            name = response.xpath('//h1[@id="h1text"]/text()').get()
            if name:
                # Clean up "- Купить в магазине..."
                name = name.split(" - ")[0].strip()

        if name:
            item["name"] = name.strip()

        # Extract image if missing
        if not item.get("image"):
            image = response.xpath('//a[@itemprop="image"]/@href').get()
            if image:
                item["image"] = response.urljoin(image)

        # Extract price if available in page but not in microdata
        # Often empty on this site if no store is selected.
        if not item.get("offers"):
            price = response.xpath('//div[@class="block_cena"]/text()').get()
            if not price:
                # Try to extract from the "Nearby stores" table if available
                price = response.xpath(
                    '//div[contains(@class, "list_paratrov")]//div[contains(text(), " руб.")]/text()'
                ).get()

            if price:
                # Clean up price (e.g. "84.90 руб./шт.")
                price = price.split(" руб.")[0].strip().replace(" ", "").replace(",", ".")
                item["offers"] = [
                    {
                        "@type": "Offer",
                        "price": price,
                        "priceCurrency": "RUB",
                        "availability": "https://schema.org/InStock",
                    }
                ]

        # Extract ref (Article/Артикул)
        ref = response.xpath('//div[contains(text(), "Артикул:")]/following-sibling::div[1]/text()').get()
        if ref:
            item["ref"] = ref.strip()

        if not item.get("name"):
            return

        yield item
