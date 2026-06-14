from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class SavegnagoBRSpider(SitemapSpider, StructuredDataSpider):
    name = "savegnago_br"
    allowed_domains = ["savegnago.com.br"]
    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q121097894",
                "name": "Savegnago Supermercados",
            }
        }
    }

    sitemap_urls = ["https://www.savegnago.com.br/sitemap.xml"]
    sitemap_rules = [
        (r"https://www.savegnago.com.br/[\w-]+/p", "parse_sd"),
    ]
