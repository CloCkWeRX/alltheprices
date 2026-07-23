import re
from urllib.parse import urlparse
from scrapy.http import Response
from scrapy.spiders import SitemapSpider
from products.items import Product
from products.linked_data_parser import LinkedDataParser
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class PrixqualityITSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Prix Quality (Italy).
    Retailer website: https://www.prixquality.com/
    Uses SitemapSpider & StructuredDataSpider.
    Wikidata: Q110434458 (Prix Quality S.p.A.)

    Sample output structured data:
    {
        "name": "Ginger Vena d’Oro",
        "website": "https://www.prixquality.com/prodotti-prix/ginger-vena-doro/",
        "ref": "703746",
        "sku": "703746",
        "image": "https://www.prixquality.com/wp-content/uploads/2021/03/703746_8032974000047_1_PX1.jpg",
        "brand": "Vena d'Oro",
        "located_in": "Italy",
        "located_in_wikidata": "Q110434458"
    }
    """

    name = "prixquality_it"
    allowed_domains = ["prixquality.com"]
    sitemap_urls = ["https://www.prixquality.com/sitemap_index.xml"]

    # We want to match only products (regular catalog products or promotional ones)
    sitemap_rules = [
        (r"/prodotti-prix/[^/]+/$", "parse_sd"),
        (r"/promo_product/[^/]+/$", "parse_sd"),
    ]

    custom_settings = {
        "USER_AGENT": FIREFOX_LATEST,
        "ROBOTSTXT_OBEY": False,
    }

    wikidata = "Q110434458"

    def sitemap_filter(self, entries):
        """
        Filter out sitemaps that do not contain products.
        This optimizes crawler startup by avoiding downloading massive sitemaps for posts/pages/tags.
        """
        for entry in entries:
            loc = entry.get("loc", "")
            if ".xml" in loc:
                if "prix_product-sitemap" in loc or "promo_product-sitemap" in loc:
                    yield entry
            else:
                yield entry

    def parse_sd(self, response: Response):
        # We can first try the standard parser (in case they add standard Product JSON-LD in the future)
        items = list(super().parse_sd(response))
        if items:
            for item in items:
                yield item
            return

        # Fallback manual extraction
        name = response.css("h1.entry-title::text").get()
        if not name:
            name = response.xpath('//meta[@property="og:title"]/@content').get()
        if name:
            if name.endswith(" - Prix"):
                name = name[:-7].strip()
            name = name.strip()

        if not name:
            return

        item = Product()
        item["name"] = name
        item["website"] = response.url

        # Extract description
        desc = response.css(".entry-content p::text").get()
        if desc:
            item["description"] = desc.strip()

        # Extract image
        image_url = response.css("article.single_blog img::attr(src)").get()
        if not image_url or "base64" in image_url:
            image_url = response.css("article.single_blog img::attr(data-src)").get()
        if not image_url:
            image_url = response.xpath('//meta[@property="og:image"]/@content').get()
        if image_url:
            item["image"] = response.urljoin(image_url)

        # Look for ld+json scripts to find breadcrumbs or other data
        ld_graph = []
        for ld_obj in LinkedDataParser.iter_linked_data(response, "json"):
            if "@graph" in ld_obj:
                ld_graph.extend(ld_obj["@graph"])
            else:
                ld_graph.append(ld_obj)

        # Parse brand from Yoast schema breadcrumbs or page
        brand = None
        for graph in ld_graph:
            if graph.get("@type") == "BreadcrumbList":
                elements = graph.get("itemListElement", [])
                if len(elements) >= 3:
                    brand = elements[2].get("name")
                    break

        if not brand:
            # Extract from breadcrumb list in page if present
            breadcrumb_elements = response.css(".breadcrumbList a::text, breadcrumb a::text, .breadcrumbList span::text").getall()
            if breadcrumb_elements and len(breadcrumb_elements) >= 3:
                brand = breadcrumb_elements[2].strip()

        if not brand:
            # Fallback to article classes
            article_class = response.css("article::attr(class)").get()
            if article_class:
                match_brand = re.search(r"product_stock-([a-zA-Z0-9-]+)", article_class)
                if match_brand:
                    brand = match_brand.group(1).replace("-", " ").title()

        if brand:
            brand = brand.strip()
            if brand.lower() not in ["prodotti prix", "homepage", "home"]:
                item["brand"] = brand

        # Parse ref / sku
        ref = None
        gtin = None
        if item.get("image"):
            filename = urlparse(item["image"]).path.split("/")[-1]
            match = re.search(r"(\d+)_(\d+)", filename)
            if match:
                ref = match.group(1)
                gtin = match.group(2)
            else:
                match_any = re.search(r"(\d+)", filename)
                if match_any:
                    ref = match_any.group(1)

        if not ref:
            post_class = response.css("article[class*='post-']::attr(class)").get()
            if post_class:
                match_post = re.search(r"post-(\d+)", post_class)
                if match_post:
                    ref = match_post.group(1)

        if not ref:
            parsed_url = urlparse(response.url)
            slug = parsed_url.path.strip("/").split("/")[-1]
            if slug:
                ref = slug

        if ref:
            item["ref"] = ref
            item["sku"] = ref

        if gtin and len(gtin) in [8, 12, 13, 14]:
            item["gtin"] = gtin

        # Run through post_process_item
        yield from self.post_process_item(item, response, {})

    def post_process_item(self, item, response, ld_data):
        item["located_in"] = "Italy"
        item["located_in_wikidata"] = "Q110434458"
        yield item
