from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class GbarbosaBRSpider(SitemapSpider, StructuredDataSpider):
    name = "gbarbosa_br"
    allowed_domains = ["gbarbosa.com.br"]
    item_attributes = {
        "extras": {
            "seller": {"@type": "Organization", "@id": "https://www.wikidata.org/wiki/Q10287817", "name": "GBarbosa"}
        }
    }

    sitemap_urls = ["https://www.gbarbosa.com.br/sitemap.xml"]
    sitemap_rules = [
        (r"https://www.gbarbosa.com.br/[\w-]+/p", "parse_sd"),
    ]
