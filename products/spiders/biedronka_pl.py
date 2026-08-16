from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class BiedronkaPLSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Biedronka Home (Poland).
    Wikidata: Q857182

    @url https://home.biedronka.pl/finish-sol-ochronna-do-zmywarki-finish-15-kg-000000000000144432.html
    @returns items 1
    @scrapes name website image ref offers
    """

    name = "biedronka_pl"
    allowed_domains = ["biedronka.pl"]
    sitemap_urls = ["https://home.biedronka.pl/sitemap_index.xml"]
    sitemap_rules = [
        (r"-[0-9]+\.html$", "parse_sd"),
    ]

    item_attributes = {
        "located_in_wikidata": "Q857182",
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q857182",
                "name": "Biedronka",
            }
        },
    }

    convert_microdata = True

    def post_process_item(self, item, response, ld_data):
        if offers := item.get("offers"):
            if isinstance(offers, dict):
                offers = [offers]
            elif not isinstance(offers, list):
                offers = []
            for offer in offers:
                if isinstance(offer, dict) and not offer.get("priceCurrency"):
                    offer["priceCurrency"] = "PLN"

        yield from super().post_process_item(item, response, ld_data)
