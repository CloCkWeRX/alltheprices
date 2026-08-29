from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class PlanetorganicGBSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Planet Organic (United Kingdom).
    Fixes #153.
    Wikidata: Q24298870

    @url https://www.planetorganic.com/products/profusion-himalayan-pink-fine-salt-shaker-140g
    @returns items 1
    @scrapes name website image ref brand price proof_currency
    """

    name = "planetorganic_gb"
    allowed_domains = ["planetorganic.com"]

    item_attributes = {
        "located_in_wikidata": "Q24298870",
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q24298870",
                "name": "Planet Organic",
            }
        },
    }

    sitemap_urls = ["https://www.planetorganic.com/sitemap.xml"]
    sitemap_rules = [
        (r"/products/([^/]+)$", "parse_sd"),
    ]
