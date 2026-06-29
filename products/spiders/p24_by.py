from urllib.parse import urljoin
from scrapy.spiders import SitemapSpider
from products.structured_data_spider import StructuredDataSpider


class P24BYSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for ПерекрёстОК (Belarus).
    Extracts product data from Schema.org Product data.
    Prices are often missing in JSON-LD and are extracted from HTML.

    Sample output:
    {
        "name": "Сыр мягкий Моцарелла mini 45% 100г пл. ОАО Савушкин продукт Беларусь",
        "website": "https://p24.by/product/4810268042782-syr-myagkiy-motsarella-mini-45-100g-pl-10-sharikov-oao-savushkin-produkt-belarus/",
        "ref": "4810268042782",
        "image": "https://p24.by/upload/slam.image/iblock/5c0/4es05cv4a2rabnl61j2yboernz47yyk5/524_524_0/1_4810268042782-90.jpg",
        "offers": [
            {
                "@type": "Offer",
                "url": "https://p24.by/product/4810268042782-syr-myagkiy-motsarella-mini-45-100g-pl-10-sharikov-oao-savushkin-produkt-belarus/",
                "priceCurrency": "BYN",
                "price": "3.29",
                "priceValidUntil": "2031-06-29",
                "availability": "https://schema.org/InStock",
                "itemCondition": "'https://schema.org/NewCondition'"
            }
        ],
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q136697102",
                "name": "ПерекрёстОК"
            }
        }
    }
    """

    name = "p24_by"
    allowed_domains = ["p24.by", "perekrestok24.by"]
    sitemap_urls = ["https://p24.by/sitemap.xml"]
    sitemap_rules = [(r"/product/(\d+)-", "parse_sd")]

    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q136697102",
                "name": "ПерекрёстОК",
            }
        }
    }

    def post_process_item(self, item, response, ld_data):
        # Fix relative website URL
        if item.get("website") and not item["website"].startswith("http"):
            item["website"] = urljoin(response.url, item["website"])

        # Ensure ref is extracted from URL if SKU is empty/missing in JSON-LD
        if not item.get("ref") or item["ref"] == item.get("website"):
            item["ref"] = self.get_ref(response.url, response)

        for offer in item.get("offers", []):
            # Fix relative offer URL
            if offer.get("url") and not offer["url"].startswith("http"):
                offer["url"] = urljoin(response.url, offer["url"])

            # Extract price from HTML if missing in JSON-LD
            if not offer.get("price"):
                price = response.css(".product-card__price-current span::text").get()
                if price:
                    offer["price"] = price.strip()
        yield item
