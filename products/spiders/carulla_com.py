from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider


class CarullaComSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Carulla (Colombia).
    Wikidata: Q5047464

    Sample output structured data:
    {
      "name": "Soda BRETANA botella vidrio x12und  (3600  ml)",
      "brand": "BRETANA",
      "image": "https://carulla.vtexassets.com/arquivos/ids/24719590/Of-Soda-Pague-9-Lleve-12-1443507_a.jpg?v=639095354124670000",
      "ref": "1443507",
      "offers": [
        {
          "@type": "Offer",
          "price": 29500,
          "priceCurrency": "COP",
          "availability": "https://schema.org/InStock",
          "itemCondition": "https://schema.org/NewCondition",
          "url": "https://www.carulla.com/of-soda-pague-9-lleve-12-365350/p",
          "seller": {
            "@type": "Organization",
            "name": "carulla"
          }
        }
      ],
      "website": "https://www.carulla.com/of-soda-pague-9-lleve-12-365350/p",
      "extras": {
        "seller": {
          "@type": "Organization",
          "@id": "https://www.wikidata.org/wiki/Q5047464",
          "name": "Carulla"
        }
      }
    }
    """

    name = "carulla_com"
    allowed_domains = ["carulla.com"]
    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q5047464",
                "name": "Carulla",
            }
        }
    }

    sitemap_urls = ["https://www.carulla.com/robots.txt"]
    sitemap_rules = [
        (r"/.*-(\d+)/p$", "parse_sd"),
        (r"/p$", "parse_sd"),
    ]
