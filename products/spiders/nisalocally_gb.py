import re
from scrapy.spiders import SitemapSpider
from products.items import Product
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class NisalocallyGBSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Nisa Locally (United Kingdom).
    Fixes #461.
    Wikidata: Q16999069
    Parent: The Co-operative Group (Q117202)

    @url https://www.nisalocally.co.uk/co-op-products/fruit-vegetables/co-op-fairtrade-bananas/
    @returns items 1
    @scrapes name website image ref brand brand_wikidata
    """

    name = "nisalocally_gb"
    allowed_domains = ["nisalocally.co.uk"]

    item_attributes = {
        "located_in_wikidata": "Q16999069",
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q16999069",
                "name": "Nisa Locally",
                "parentOrganization": {
                    "@type": "Organization",
                    "@id": "https://www.wikidata.org/wiki/Q117202",
                    "name": "The Co-operative Group",
                },
            }
        },
    }

    custom_settings = {
        "USER_AGENT": FIREFOX_LATEST,
        "ROBOTSTXT_OBEY": False,
    }

    sitemap_urls = [
        "https://www.nisalocally.co.uk/sitemap.xml",
    ]
    sitemap_rules = [
        (r"/co-op-products/[^/]+/[^/]+/$", "parse_sd"),
    ]

    def iter_linked_data(self, response):
        # Nisa's product pages don't have standard Product JSON-LD structured data.
        # So we implement a custom parsing logic as a fallback here.
        name = response.css(".product-detail span.title::text").get()
        if name:
            name = name.strip()

            description_list = response.css(".product-detail-descr p::text").getall()
            description = " ".join([d.strip() for d in description_list if d.strip()]) if description_list else None

            image_rel = response.css(".product-detail-image img::attr(src)").get()
            image = response.urljoin(image_rel) if image_rel else None

            ref = None
            if image_rel:
                m = re.search(r"/([0-9]{8,14})\.jpg", image_rel)
                if m:
                    ref = m.group(1)

            brand = None
            brand_wikidata = None
            if name:
                name_lower = name.lower()
                if name_lower.startswith("co-op") or name_lower.startswith("co op") or "co-op" in name_lower or "co op" in name_lower:
                    brand = "Co-op"
                    brand_wikidata = "Q117202"

            yield {
                "@type": "Product",
                "name": name,
                "description": description,
                "image": image,
                "sku": ref,
                "brand": brand,
                "brand_wikidata": brand_wikidata,
            }

    def post_process_item(self, item, response, ld_data):
        if not item.get("ref") and (sku := item.get("sku")):
            item["ref"] = sku

        # Copy over brand and brand_wikidata if present in raw ld_data dict
        if "brand" in ld_data and ld_data["brand"]:
            item["brand"] = ld_data["brand"]
        if "brand_wikidata" in ld_data and ld_data["brand_wikidata"]:
            item["brand_wikidata"] = ld_data["brand_wikidata"]

        yield from super().post_process_item(item, response, ld_data)
