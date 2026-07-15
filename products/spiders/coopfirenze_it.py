import re
from scrapy import Request
from scrapy.spiders import SitemapSpider
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class CoopfirenzeITSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Coop Firenze (Italy).
    Wikidata: Q4004707 (Unicoop Firenze)

    Sample output structured data:
    {
        "name": "Cornetti classici 6 pz 240 gr",
        "website": "https://prenotalaspesa.coopfirenze.it/colazione/merendine/classiche/0100627301900.html",
        "ref": "0100627301900",
        "image": "https://s7g10.scene7.com/is/image/unicoopfirenze/unicoop-dam/010062/73/01900/01/01/6273019_922452.jpg",
        "offers": [
            {
                "@type": "Offer",
                "url": "https://prenotalaspesa.coopfirenze.it/colazione/merendine/classiche/0100627301900.html",
                "priceCurrency": "EUR",
                "price": "2.43",
                "availability": "http://schema.org/InStock"
            }
        ],
        "price": "2.43",
        "proof_currency": "EUR",
        "located_in": "Italy",
        "located_in_wikidata": "Q4004707"
    }
    """

    name = "coopfirenze_it"
    allowed_domains = ["coopfirenze.it", "prenotalaspesa.coopfirenze.it"]
    sitemap_urls = ["https://prenotalaspesa.coopfirenze.it/sitemap_index.xml"]
    sitemap_rules = [
        (r"/([^/]+)/$", "parse_category"),
    ]

    custom_settings = {
        "USER_AGENT": FIREFOX_LATEST,
        "ROBOTSTXT_OBEY": False,
    }

    def parse_category(self, response):
        """
        Extracts product URLs from category page.
        Product URLs look like: /category/.../13-digit-sku.html
        """
        product_links = response.css("a::attr(href)").getall()
        for link in product_links:
            if re.search(r"/\d+\.html$", link):
                product_url = response.urljoin(link)
                yield Request(product_url, callback=self.parse_sd)

    def post_process_item(self, item, response, ld_data):
        item["located_in"] = "Italy"
        item["located_in_wikidata"] = "Q4004707"

        # Resolve relative website URL
        if item.get("website") and not item["website"].startswith("http"):
            item["website"] = response.urljoin(item["website"])

        # Promotes price and currency from offers to top level fields
        if item.get("offers"):
            offers = item["offers"]
            if isinstance(offers, dict):
                offers = [offers]
            if offers:
                offer = offers[0]
                item["price"] = offer.get("price")
                item["proof_currency"] = offer.get("priceCurrency")

        # Clean relative URLs in offers
        for offer in item.get("offers", []):
            if offer.get("url") and isinstance(offer["url"], str) and not offer["url"].startswith("http"):
                offer["url"] = response.urljoin(offer["url"])

        yield item
