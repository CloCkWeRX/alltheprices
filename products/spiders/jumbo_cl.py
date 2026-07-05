from scrapy.spiders import SitemapSpider
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST

class JumboCLSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Jumbo (Chile).
    Extracts product data from Schema.org JSON-LD.

    Sample output:
    {
        "brand": "Evian",
        "brand_wikidata": "Q6310864",
        "extras": {
            "@source_uri": "https://www.jumbo.cl/agua-mineral-sin-gas-evian-1-l-botella-desechable/p",
            "owner": {
                "@id": "https://www.wikidata.org/wiki/Q1053351",
                "@type": "Organization",
                "name": "Cencosud"
            }
        },
        "gtin": "61314000070",
        "image": "https://jumbocl.vtexassets.com/arquivos/ids/297560-250-250/Principal-3453.jpg?v=638775740696900000",
        "name": "Agua Evian Mineral Sin Gas 1 L",
        "offers": [
            {
                "@type": "Offer",
                "availability": "https://schema.org/InStock",
                "itemCondition": "https://schema.org/NewCondition",
                "price": "2392",
                "priceCurrency": "CLP",
                "seller": {
                    "@type": "Organization",
                    "name": "Jumbo.cl"
                },
                "url": "https://jumbo.cl/agua-mineral-sin-gas-evian-1-l-botella-desechable/p"
            }
        ],
        "ref": "12",
        "website": "https://www.jumbo.cl/agua-mineral-sin-gas-evian-1-l-botella-desechable/p"
    }
    """

    name = "jumbo_cl"
    allowed_domains = ["jumbo.cl"]
    user_agent = FIREFOX_LATEST

    sitemap_urls = ["https://www.jumbo.cl/sitemap.xml"]
    sitemap_rules = [
        (r"/p$", "parse_sd"),
    ]

    item_attributes = {
        "brand_wikidata": "Q6310864",
        "extras": {
            "owner": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q1053351",
                "name": "Cencosud",
            }
        },
    }

    def post_process_item(self, item, response, ld_data, **kwargs):
        if "gtin" in ld_data:
            item["gtin"] = ld_data["gtin"]
        if "brand" in ld_data and isinstance(ld_data["brand"], dict):
            item["brand"] = ld_data["brand"].get("name")
        yield item
