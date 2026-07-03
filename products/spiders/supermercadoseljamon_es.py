from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class SupermercadoseljamonESSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Supermercados El Jamón (Spain).
    Extracts product data from Schema.org Product data in JSON-LD.

    Sample output:
    {
      "extras": {
        "seller": {
          "@id": "https://www.wikidata.org/wiki/Q6135982",
          "@type": "Organization",
          "name": "Supermercados El Jamón"
        }
      },
      "image": "https://www.supermercadoseljamon.com/documents/10180/892067/28010108_G.jpg",
      "name": "crema vinagre balsámico de módena 0%, 400g",
      "offers": [
        {
          "@type": "Offer",
          "availability": "InStock",
          "itemCondition": "http://schema.org/NewCondition",
          "price": "1.85",
          "priceCurrency": "EUR"
        }
      ],
      "ref": "28010108",
      "website": "https://www.supermercadoseljamon.com/detalle/-/Producto/crema-vinagre-balsamico-de-modena-0--400g/28010108"
    }
    """

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
