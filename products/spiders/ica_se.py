from scrapy.spiders import SitemapSpider
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class IcaSESpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for ICA Sweden (handla.ica.se).
    Wikidata: Q1663776 (ICA Gruppen)
    Fix #467.
    """

    name = "ica_se"
    allowed_domains = ["handla.ica.se"]
    sitemap_urls = ["https://handla.ica.se/sitemap"]
    sitemap_rules = [
        (r"/produkt/(\d+)", "parse_sd"),
    ]

    custom_settings = {
        "USER_AGENT": FIREFOX_LATEST,
        "ROBOTSTXT_OBEY": False,
    }

    item_attributes = {
        "proof_currency": "SEK",
        "located_in_wikidata": "Q1663776",
        "brand_wikidata": "Q1663776",
    }

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["proof_currency"] = "SEK"
        item["located_in_wikidata"] = "Q1663776"

        # Default brand to ICA if not specified
        if not item.get("brand"):
            item["brand"] = "ICA"

        # Only map brand_wikidata to ICA if the brand is indeed ICA
        brand_name = item.get("brand") or ""
        if "ica" in brand_name.lower():
            item["brand_wikidata"] = "Q1663776"
        else:
            item.pop("brand_wikidata", None)

        # Map mpn or productId to gtin / ref if available
        if ld_data.get("mpn"):
            item["gtin"] = str(ld_data["mpn"]).strip()

        if ld_data.get("productId"):
            item["ref"] = str(ld_data["productId"]).strip()
            item["sku"] = str(ld_data["productId"]).strip()

        yield item
