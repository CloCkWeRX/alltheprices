from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class MixmarktExpressDESpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Mix Markt (Germany/Europe).
    Wikidata: Q327854

    @url https://www.mixmarkt-express.eu/detail/index/sArticle/4491
    @returns items 1
    @scrapes name website image ref offers
    """

    name = "mixmarkt_express_de"
    allowed_domains = ["mixmarkt-express.eu"]
    sitemap_urls = ["https://www.mixmarkt-express.eu/sitemap.xml"]
    sitemap_rules = [
        (r"/sArticle/\d+", "parse_sd"),
    ]

    item_attributes = {
        "located_in_wikidata": "Q327854",
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q327854",
                "name": "Mix Markt",
            }
        },
    }

    convert_microdata = True

    def post_process_item(self, item, response, ld_data):
        # Set currency to EUR explicitly if missing or unparsed
        if offers := item.get("offers"):
            if isinstance(offers, dict):
                offers = [offers]
            elif not isinstance(offers, list):
                offers = []
            for offer in offers:
                if isinstance(offer, dict) and not offer.get("priceCurrency"):
                    offer["priceCurrency"] = "EUR"

        # Ensure ref is populated (sku/ref)
        if not item.get("ref"):
            if sku := item.get("sku"):
                item["ref"] = sku
            else:
                # Fallback to the ID from the URL
                import re

                match = re.search(r"/sArticle/(\d+)", response.url)
                if match:
                    item["ref"] = match.group(1)

        yield from super().post_process_item(item, response, ld_data)
