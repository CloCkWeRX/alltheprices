import re
import chompjs
from scrapy.http import Response
from scrapy.spiders import SitemapSpider
from products.items import Product
from products.structured_data_spider import StructuredDataSpider

class PolomarketPLSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for POLOmarket (Poland).
    Wikidata: Q11821937
    """

    name = "polomarket_pl"
    allowed_domains = ["polomarket.pl"]
    sitemap_urls = ["https://www.polomarket.pl/sitemap.xml"]
    sitemap_rules = [
        (r"/produkty/([^/]+)$", "parse_sd"),
    ]

    item_attributes = {
        "brand": "POLOmarket",
        "brand_wikidata": "Q11821937",
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q11821937",
                "name": "POLOmarket",
            }
        }
    }

    def iter_linked_data(self, response: Response):
        # Try to extract data from window.__NUXT__
        nuxt_match = re.search(r'window\.__NUXT__=\(function\(.*?\)\{return (\{.*?\})\}\)\(.*\);', response.text, re.DOTALL)
        if nuxt_match:
            try:
                data = chompjs.parse_js_object(nuxt_match.group(1))
                # The data structure in Nuxt can be complex.
                # Based on the grep: data:[{productDetails:{...}}]
                # We need to find the productDetails.

                product_details = None
                if "data" in data and isinstance(data["data"], list):
                    for entry in data["data"]:
                        if "productDetails" in entry:
                            product_details = entry["productDetails"]
                            break

                if product_details:
                    name = product_details.get("name")
                    # Price handling
                    # In some Nuxt sites, prices are indices into a larger array.
                    # But here it seems to be directly in the object or in the function arguments.
                    # If it's a variable name like 'a', 'b', it means it was passed as an argument.
                    # chompjs might not resolve these arguments easily without the full context.

                    # Fallback to HTML if Nuxt parsing is incomplete
                    if not name or isinstance(name, str) and len(name) < 2:
                         name = response.css('h1::text').get()

                    price = product_details.get("price")
                    # If price is not a number, it might be an argument we can't resolve easily here.

                    image = product_details.get("image")
                    if image and not image.startswith('http'):
                        image = response.urljoin(image)

                    if name:
                        yield {
                            "@type": "Product",
                            "name": name.strip() if name else None,
                            "image": image,
                            "sku": product_details.get("eanCode"),
                            "offers": {
                                "@type": "Offer",
                                "price": price if isinstance(price, (int, float)) else None,
                                "priceCurrency": "PLN",
                                "availability": "https://schema.org/InStock",
                            }
                        }
                        return
            except Exception:
                self.logger.debug("Failed to parse Nuxt state", exc_info=True)

        # Fallback to Bespoke extraction from HTML
        name = response.css('h1::text').get()
        if name:
            image = response.css('img[src*="filer_public"]::attr(src)').get()
            if image and not image.startswith('http'):
                image = response.urljoin(image)

            yield {
                "@type": "Product",
                "name": name.strip(),
                "image": image,
                "offers": {
                    "@type": "Offer",
                    "priceCurrency": "PLN",
                    "availability": "https://schema.org/InStock",
                }
            }

    def post_process_item(self, item: Product, response: Response, ld_data: dict, **kwargs):
        if not item.get("ref"):
            item["ref"] = response.url.split("/")[-1]

        if item.get("name"):
            item["name"] = item["name"].strip()

        # If price is missing from iter_linked_data, try to find it in HTML
        if item.get("offers") and len(item["offers"]) > 0 and not item["offers"][0].get("price"):
            # POLOmarket often shows price with integer and fraction separated or in a specific way
            # Try to find common patterns
            price_text = response.xpath('//div[contains(@class, "price")]//text()').getall()
            price_text = "".join(price_text).strip()
            if price_text:
                # Regex for price like 3,99 or 3.99
                match = re.search(r'(\d+)[,.](\d{2})', price_text)
                if match:
                    item["offers"][0]["price"] = f"{match.group(1)}.{match.group(2)}"

        yield item
