from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider
from products.user_agents import BROWSER_DEFAULT


class ContinentePTSpider(SitemapSpider, StructuredDataSpider):
    name = "continente_pt"
    allowed_domains = ["continente.pt"]
    user_agent = BROWSER_DEFAULT

    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q2995683",
                "name": "Continente",
            }
        }
    }

    sitemap_urls = [
        "https://www.continente.pt/sitemap-custom_sitemap_1-product.xml",
        "https://www.continente.pt/sitemap-custom_sitemap_12-product.xml",
        "https://www.continente.pt/sitemap-custom_sitemap_16-product.xml",
        "https://www.continente.pt/sitemap-custom_sitemap_20-product.xml",
        "https://www.continente.pt/sitemap-custom_sitemap_4-product.xml",
        "https://www.continente.pt/sitemap-custom_sitemap_8-product.xml",
    ]
    sitemap_rules = [
        (r"/produto/.*-(\d+)\.html", "parse"),
    ]
