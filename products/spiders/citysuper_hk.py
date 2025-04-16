from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class CitysuperHKSpider(SitemapSpider, StructuredDataSpider):
    name = "citysuper_hk"
    allowed_domains = ["online.citysuper.com.hk"]
    item_attributes = {
        "extras": {
            "seller": {"@type": "Organization", "@id": "https://www.wikidata.org/wiki/Q5124105", "name": "C!ty'super"}
        }
    }

    sitemap_urls = ["https://online.citysuper.com.hk/sitemap.xml"]
    sitemap_rules = [
        (r"https://online.citysuper.com.hk/products/[\w-]+", "parse_sd"),
    ]
