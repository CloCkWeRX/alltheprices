from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class SupermercadoseljamonESSpider(SitemapSpider, StructuredDataSpider):
    name = "supermercadoseljamon_es"
    allowed_domains = ["www.supermercadoseljamon.com"]
    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q6135982",
                "name": "Supermercados El Jamón",
            }
        }
    }

    sitemap_urls = ["https://www.supermercadoseljamon.com/sitemap.xml"]
    sitemap_rules = [
        (r"/detalle/-/Producto/.*?/(\d+)", "parse_sd"),
    ]

    json_parser = "chompjs"

    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "DEFAULT_REQUEST_HEADERS": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
        },
    }
