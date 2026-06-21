from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from products.items import Product
from products.structured_data_spider import StructuredDataSpider


class SemishagoffOrgSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for semishagoff.org.
    The site uses Bitrix and has limited schema.org/Product data, so we manually
    extract name, price, and image.

    Sample output:
    {
        "extras": {
            "@source_uri": "https://www.semishagoff.org/catalog/molochnaya-produkciya/smetana/biosmetana-rogachev-12-350g-bzmj-belarus/",
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q58003374",
                "name": "Semishagoff"
            }
        },
        "name": "Биосметана 'Рогачевъ' 12% 350г БЗМЖ, Беларусь",
        "website": "https://www.semishagoff.org/catalog/molochnaya-produkciya/smetana/biosmetana-rogachev-12-350g-bzmj-belarus/",
        "ref": "64090",
        "image": "https://www.semishagoff.org/upload/iblock/938/ep2fbt6kqjeumtswqg121j9waog0ciiz/78947.jpg",
        "offers": [
            {
                "@type": "Offer",
                "price": "76.99",
                "priceCurrency": "RUB",
                "availability": "https://schema.org/InStock"
            }
        ]
    }
    """

    name = "semishagoff_org"
    allowed_domains = ["semishagoff.org"]
    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q58003374",
                "name": "Semishagoff",
            }
        }
    }

    sitemap_urls = ["https://www.semishagoff.org/sitemap.xml"]
    sitemap_rules = [
        (r"/catalog/[^/]+/[^/]+/[^/]+/", "parse_sd"),
    ]

    wanted_types = ["Product", "IndividualProduct", "BreadcrumbList"]

    def sitemap_filter(self, entries):
        for entry in entries:
            entry["loc"] = entry["loc"].replace("http://semishagoff.org", "https://www.semishagoff.org")
            yield entry

    def post_process_item(self, item: Product, response: Response, ld_data: dict, **kwargs):
        """Manual extraction since schema.org/Product is missing."""
        # BreadcrumbList might be present, but we want Product data.
        # If we got a Product from ld_data, item will have some fields.
        # But here it's mostly missing, so we populate it.

        name = response.xpath('//h1[@class="product-page__title"]/text()').get()
        if name:
            item["name"] = name.strip()

        # Always try to get a better image than the default og:image or BreadcrumbList fallback
        product_image = response.xpath('//div[@class="product-page__main-img"]/img/@src').get()
        if product_image:
            item["image"] = response.urljoin(product_image)

        price = response.xpath('//div[@class="product-page__price-new"]/text()').get()
        if price:
            item["offers"] = [
                {
                    "@type": "Offer",
                    "price": price.strip().replace(" ", ""),
                    "priceCurrency": "RUB",
                    "availability": "https://schema.org/InStock",
                }
            ]

        # Prefer numeric ID from button if available
        ref = response.xpath('//button[@data-cart-good]/@data-cart-good').get()
        if ref:
            item["ref"] = ref

        # If we didn't get a name, it's probably not a product page we can parse
        if not item.get("name"):
            return

        yield item
