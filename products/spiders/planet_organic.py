from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class PlanetOrganicSpider(SitemapSpider, StructuredDataSpider):
    name = "planet_organic"
    allowed_domains = ["planetorganic.com"]
    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q24298870",
                "name": "Planet Organic",
            }
        }
    }

    sitemap_urls = ["https://www.planetorganic.com/sitemap.xml"]
    sitemap_rules = [
        (r"https://www.planetorganic.com/products/[\w-]+", "parse_sd"),
    ]
