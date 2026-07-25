import json
import re
from urllib.parse import urljoin
from scrapy import Request
from scrapy.spiders import SitemapSpider
from products.structured_data_spider import StructuredDataSpider
from products.items import Product
from products.user_agents import FIREFOX_LATEST

class SelverEESpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Selver (Estonia).
    Uses the sitemap to discover product URLs, but queries the public Vue Storefront Elasticsearch API
    to retrieve product details directly. This is extremely fast, reliable and conforms to the
    Roadmap's preference for structured JSON APIs.
    Wikidata: Q3771177 (Selver)
    """

    name = "selver_ee"
    allowed_domains = ["selver.ee"]
    sitemap_urls = ["https://www.selver.ee/sitemap.xml"]

    # We match product detail pages which are flat path segments.
    # To avoid matching category listings (which can also be flat, but usually have no numeric suffix),
    # we match URLs that are not main categories and typically end with a name or id.
    # Selver sitemap has many types. We can define broad rules or just handle them dynamically.
    sitemap_rules = [
        (r"https://www.selver.ee/([a-z0-9-]+)$", "parse_product"),
        (r"https://www.selver.ee/ru/([a-z0-9-]+)$", "parse_product"),
    ]

    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": FIREFOX_LATEST,
    }

    def sitemap_filter(self, entries):
        for entry in entries:
            loc = entry.get("loc", "")
            # Skip common CMS, informational pages, or obvious category paths to speed up discovery
            if any(term in loc for term in [
                "/uudis-", "/kontakt", "/selverist", "/partnerkaart", "/klienditeenindus",
                "/retseptid", "/kampaania", "/tooted", "/kuivained-hoidised", "/joogid",
                "/enesehooldustarbed", "/majapidamis-ja-kodukaubad", "/leivad-saiad-kondiitritooted",
                "/piimatooted-munad-void", "/liha-ja-kalatooted", "/valmistoidud",
                "/puu-ja-koogiviljad", "/kylmutatud-tooted", "/maiustused-kupsised-naksid",
                "/lastekaubad", "/lemmikloomakaubad", "/vabaajakaubad"
            ]):
                continue
            # Also avoid the homepages or simple /ru/
            if loc in ["https://www.selver.ee/", "https://www.selver.ee//", "https://www.selver.ee/ru/", "https://www.selver.ee/ru//"]:
                continue
            yield entry

    def parse_product(self, response):
        # Extract the url_key from URL
        url = response.url
        match = re.search(r"https://www.selver.ee/(?:ru/)?([a-z0-9-]+)$", url)
        if not match:
            return

        url_key = match.group(1)
        api_url = f"https://www.selver.ee/api/catalog/vue_storefront_catalog_et/product/_search?q=url_key:{url_key}"

        # We make a request to the Vue Storefront catalog API
        yield Request(
            api_url,
            callback=self.parse_api_response,
            meta={"original_url": url},
            cb_kwargs={"url_key": url_key}
        )

    def parse_api_response(self, response, url_key):
        try:
            data = json.loads(response.text)
        except Exception:
            self.logger.warning(f"Failed to parse JSON response from {response.url}")
            return

        hits = data.get("hits", {}).get("hits", [])
        if not hits:
            self.logger.info(f"No API product found for url_key: {url_key}")
            return

        source = hits[0].get("_source", {})

        # Parse fields
        name = source.get("name")
        if not name:
            return

        ref = source.get("sku") or source.get("id") or str(source.get("entity_id"))

        # Image is typically under "image" but we need the correct base domain path
        image_path = source.get("image")
        image_url = None
        if image_path:
            # Selver media catalog path
            image_url = urljoin("https://www.selver.ee/media/catalog/product/", image_path.lstrip("/"))

        # Price parsing
        price = None
        # Vue storefront catalog has prices array and final_price/regular_price
        if "regular_price" in source:
            price = source["regular_price"]
        elif "price" in source:
            price = source["price"]

        if price is not None:
            try:
                price = float(price)
            except ValueError:
                price = None

        brand = None
        # brand attribute might be an ID or name, but they often have manufacturer or name containing brand
        # Let's check product_brand or manufacturer or extract from name
        brand_val = source.get("product_brand")
        if isinstance(brand_val, str):
            brand = brand_val
        elif item_brand := source.get("brand"):
            if isinstance(item_brand, dict):
                brand = item_brand.get("name")
            elif isinstance(item_brand, str):
                brand = item_brand

        # Fallback to name-based brand extraction
        if not brand and name:
            # Usually brand is uppercase or separate word in name
            # Selver names are like: "Kohupiimadessert vaarikatäidisega, JEPPI, 38 g"
            # Or "Kommid 36 Maitset Gurmee tuubis, JELLY BEAN, 90g"
            # If we split by comma, the brand is often the second or third element
            parts = [p.strip() for p in name.split(",")]
            for part in parts:
                if part.isupper() and len(part) > 1:
                    brand = part
                    break

        item = Product(
            name=name,
            website=response.meta.get("original_url"),
            ref=ref,
            gtin=source.get("product_main_ean"),
            brand=brand,
            description=source.get("description"),
            image=image_url,
            price=price,
            proof_currency="EUR",
            located_in_wikidata="Q3771177"
        )

        # Only set brand_wikidata dynamically if the brand is actually Selver's private label
        # Selver's private labels are usually "Selver", "Selveri Köök", "Selveri" or similar.
        if brand and any(keyword in brand.lower() for keyword in ["selver"]):
            item["brand_wikidata"] = "Q3771177"

        yield item
