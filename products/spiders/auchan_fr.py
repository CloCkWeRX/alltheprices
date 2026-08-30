from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class AuchanFRSpider(SitemapSpider, StructuredDataSpider):
    name = "auchan_fr"
    allowed_domains = ["auchan.fr"]
    user_agent = FIREFOX_LATEST
    convert_microdata = True

    sitemap_urls = ["https://www.auchan.fr/sitemaps/sitemap-products.xml"]
    sitemap_follow = [r"sitemap-products.*\.xml"]
    sitemap_rules = [
        (r"/pr-([A-Z0-9]+)$", "parse_sd"),
    ]

    item_attributes = {
        "proof_currency": "EUR",
        "located_in_wikidata": "Q758603",
    }

    def post_process_item(self, item, response, ld_data):
        if not item.get("proof_currency"):
            item["proof_currency"] = "EUR"

        # Check nested offers if top-level price is missing
        if not item.get("price"):
            offers = ld_data.get("offers") if isinstance(ld_data, dict) else None
            if isinstance(offers, list) and len(offers) > 0:
                offer = offers[0]
            elif isinstance(offers, dict):
                offer = offers
            else:
                offer = {}

            price = offer.get("price")
            if price is not None:
                try:
                    item["price"] = float(str(price).replace(",", "."))
                except ValueError:
                    pass

            if offer.get("priceCurrency"):
                item["proof_currency"] = offer.get("priceCurrency")

        yield item
