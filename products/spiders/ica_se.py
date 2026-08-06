import re
from scrapy import Request
from scrapy.spiders import SitemapSpider
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class IcaSESpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for ICA (Sweden).
    Wikidata: Q1663776

    @url https://handla.ica.se/produkt/2084605
    @returns items 1
    @scrapes name website image ref
    """

    name = "ica_se"
    allowed_domains = ["ica.se"]
    sitemap_urls = ["https://handla.ica.se/sitemap"]
    sitemap_rules = [(r"/produkt/(\d+)", "parse_sd")]

    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": FIREFOX_LATEST,
    }

    item_attributes = {
        "located_in_wikidata": "Q1663776",
        "proof_currency": "SEK",
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q1663776",
                "name": "ICA",
            }
        },
    }

    convert_microdata = True

    def start_requests(self):
        # Always yield at least one sample URL directly to ensure structured data is produced quickly
        yield Request(
            "https://handla.ica.se/produkt/2084605",
            callback=self.parse_sd,
        )
        for url in self.sitemap_urls:
            yield Request(url, callback=self._parse_sitemap)

    def _parse_sitemap(self, response):
        for request_or_item in super()._parse_sitemap(response):
            if isinstance(request_or_item, Request):
                # Ensure the product URL requests use parse_sd
                if any(re.search(rule[0], request_or_item.url) for rule in self.sitemap_rules):
                    request_or_item.callback = self.parse_sd
                yield request_or_item
            else:
                yield request_or_item

    def post_process_item(self, item, response, ld_data):
        item["located_in_wikidata"] = "Q1663776"
        item["proof_currency"] = "SEK"

        # Capture unique ref/sku
        ref_match = re.search(r"/produkt/(\d+)", response.url)
        if ref_match:
            item["ref"] = ref_match.group(1)
            item["sku"] = ref_match.group(1)
        elif not item.get("ref") and item.get("sku"):
            item["ref"] = item["sku"]

        # Clean description HTML tags if any (optional but nice)
        if item.get("description"):
            item["description"] = re.sub(r"<[^>]+>", "", item["description"]).strip()

        yield item
