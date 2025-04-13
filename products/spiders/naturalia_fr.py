from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class NaturaliaFRSpider(SitemapSpider, StructuredDataSpider):
    name = "naturalia_fr"
    allowed_domains = ["naturalia.fr"]

    sitemap_urls = ["https://www.naturalia.fr/sitemap.xml"]
    sitemap_rules = [
        (r"https://www.naturalia.fr/produit/[\w-]+", "parse_sd"),
    ]
