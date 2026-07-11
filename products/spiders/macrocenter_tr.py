from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class MacrocenterTRSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Macrocenter (Turkey).
    Wikidata: Q123194881
    """

    name = "macrocenter_tr"
    allowed_domains = ["macrocenter.com.tr"]
    user_agent = FIREFOX_LATEST

    sitemap_urls = ["https://www.macrocenter.com.tr/hermes/api/sitemaps/sitemap.xml"]
    sitemap_rules = [
        (r"-p-([a-z0-9]+)$", "parse_sd"),
    ]

    def iter_linked_data(self, response):
        from products.linked_data_parser import LinkedDataParser

        for ld_obj in LinkedDataParser.iter_linked_data(response, self.json_parser):
            if not ld_obj.get("@type"):
                continue

            types = ld_obj["@type"]
            if not isinstance(types, list):
                types = [types]

            types = [LinkedDataParser.clean_type(t) for t in types]

            # Standard Product detection
            is_product = False
            for wanted_types in self.wanted_types:
                if isinstance(wanted_types, list):
                    if all(wanted in types for wanted in wanted_types):
                        is_product = True
                        break
                elif wanted_types in types:
                    is_product = True
                    break

            if is_product:
                yield ld_obj
                continue

            # Migros/Macrocenter specific nesting: WebPage -> mainEntity -> offers -> itemOffered
            if "webpage" in types:
                main_entity = ld_obj.get("mainEntity", {})
                offers_wrapper = main_entity.get("offers", {})
                items = offers_wrapper.get("itemOffered", [])
                if isinstance(items, dict):
                    items = [items]
                for item in items:
                    item_types = item.get("@type", [])
                    if not isinstance(item_types, list):
                        item_types = [item_types]
                    item_types = [LinkedDataParser.clean_type(t) for t in item_types]

                    if any(wanted in item_types for wanted in self.wanted_types):
                        yield item

    def post_process_item(self, item, response, ld_data):
        item["located_in_wikidata"] = "Q123194881"

        if not item.get("price") and "offers" in ld_data:
            offers = ld_data["offers"]
            if isinstance(offers, list):
                offers = offers[0]
            if isinstance(offers, dict):
                item["price"] = offers.get("price")
                item["proof_currency"] = offers.get("priceCurrency")

        yield item
