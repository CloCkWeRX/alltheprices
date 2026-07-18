import re
import json
import chompjs
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from products.items import Product
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST

class SokmarketTRSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Şok Market (Turkey) (Q19613992).
    Fix #155.

    Sample output:
    {
        "name": "Eti Popkek Limonlu 60 g",
        "website": "https://www.sokmarket.com.tr/eti-popkek-limonlu-60-g-p-2120",
        "image": "https://images.ceptesok.com/product-assets/sub-folder/f9d3e694-e126-4311-998a-ecc6735c909a.png",
        "ref": "2120",
        "sku": "2120",
        "brand": "ETİ",
        "offers": [
            {
                "@type": "Offer",
                "priceCurrency": "TRY",
                "price": "14.95",
                "availability": "https://schema.org/InStock",
                "sku": "2120",
                "seller": {
                    "@type": "Organization",
                    "name": "Şok Market"
                }
            }
        ],
        "price": 14.95,
        "proof_currency": "TRY",
        "located_in_wikidata": "Q19613992"
    }
    """
    name = "sokmarket_tr"
    allowed_domains = ["sokmarket.com.tr"]
    sitemap_urls = ["https://www.sokmarket.com.tr/sitemap/sitemap.xml"]
    sitemap_rules = [
        (r"-p-(\d+)$", "parse_sd"),
    ]

    custom_settings = {
        "USER_AGENT": FIREFOX_LATEST,
        "ROBOTSTXT_OBEY": False,
    }

    def sitemap_filter(self, entries):
        for entry in entries:
            loc = entry["loc"]
            if ".xml" in loc:
                # For sitemap files, only allow product sub-sitemaps
                if "product" in loc:
                    yield entry
            else:
                # For actual URLs inside sitemaps, we yield them so sitemap_rules can match them
                yield entry

    def parse_sd(self, response: Response):
        # Sok Market does not have standard Schema.org JSON-LD in static HTML,
        # but it utilizes Next.js with hydration scripts containing full product data.
        # We parse the self.__next_f.push scripts using chompjs.
        html = response.text
        pushes = re.findall(r'self\.__next_f\.push\(\[1,\"(.*?)\"\]\)', html)
        decoded_pushes = []
        for p in pushes:
            try:
                # Decode properly to support Turkish characters and unicode escapes
                s = p.encode('latin-1', 'backslashreplace').decode('unicode_escape')
                decoded_pushes.append(s)
            except Exception:
                pass

        pushed_text = "".join(decoded_pushes)
        product_data = None
        initial_variant = None

        for m in re.finditer(r'\"initialVariant\"', pushed_text):
            start = m.start()
            # Try to parse the JS object starting around initialVariant
            for offset in range(50, 0, -5):
                try:
                    sub = pushed_text[start - offset:]
                    obj = chompjs.parse_js_object(sub)
                    if isinstance(obj, list):
                        for item in obj:
                            if isinstance(item, dict) and 'productData' in item:
                                product_data = item['productData']
                                initial_variant = item.get('initialVariant')
                                break
                    elif isinstance(obj, dict) and 'productData' in obj:
                        product_data = obj['productData']
                        initial_variant = obj.get('initialVariant')
                    if product_data:
                        break
                except Exception:
                    pass
            if product_data:
                break

        if not product_data:
            return

        prod = product_data.get("product", {})
        name = prod.get("name")
        if not name:
            return

        ref = prod.get("id")
        brand = prod.get("brand", {}).get("name")

        # Handle image
        image_url = None
        images = prod.get("images", [])
        if images and isinstance(images, list):
            img_info = images[0]
            host = img_info.get("host", "").rstrip("/")
            path = img_info.get("path", "").lstrip("/")
            if host and path:
                image_url = f"{host}/{path}"
            elif path:
                image_url = f"https://images.ceptesok.com/{path}"

        # Handle price/offers
        price = None
        currency = "TRY"
        if initial_variant:
            prices = initial_variant.get("prices", {})
            discounted = prices.get("discounted", {})
            if discounted:
                price_val = discounted.get("value")
                if price_val is not None:
                    try:
                        price = float(price_val)
                    except ValueError:
                        pass
                currency = discounted.get("currency", "TRY")

        offers = []
        if price is not None:
            offers.append({
                "@type": "Offer",
                "priceCurrency": currency,
                "price": str(price),
                "availability": "https://schema.org/InStock" if initial_variant.get("hasStock", True) else "https://schema.org/OutOfStock",
                "sku": ref,
                "seller": {
                    "@type": "Organization",
                    "name": "Şok Market"
                }
            })

        item = Product(
            name=name,
            website=response.url,
            image=image_url,
            ref=ref,
            sku=ref,
            brand=brand,
            offers=offers,
            price=price,
            proof_currency=currency,
            located_in_wikidata="Q19613992"
        )

        yield item
