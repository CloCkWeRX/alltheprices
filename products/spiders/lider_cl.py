import re

from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class LiderCLSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Líder (Chile).
    Extracts product data from Schema.org Product data in JSON-LD.

    Sample output:
    {
        "extras": {
            "seller": {
                "@id": "https://www.wikidata.org/wiki/Q6711261",
                "@type": "Organization",
                "name": "Líder"
            }
        },
        "image": "https://i5.walmartimages.cl/asr/7842447b-67c8-4982-8dc1-4792f7cf8cca.c9be1ba533dfaf455e4199295d5a4ed9.jpeg?odnHeight=2000&odnWidth=2000&odnBg=ffffff",
        "name": "Libro Libro Tinisima",
        "offers": [
            {
                "@type": "Offer",
                "availability": "https://schema.org/InStock",
                "availableDeliveryMethod": "https://schema.org/OnSitePickup",
                "itemCondition": "https://schema.org/NewCondition",
                "price": 25900,
                "priceCurrency": "CLP",
                "url": "https://www.lider.cl/ip/libros/libro-libro-tinisima/00978956629177"
            }
        ],
        "ref": "00978956629177",
        "website": "https://www.lider.cl/ip/libros/libro-libro-tinisima/00978956629177"
    }
    """

    name = "lider_cl"
    allowed_domains = ["lider.cl"]
    user_agent = FIREFOX_LATEST

    custom_settings = {
        # Robots.txt blocks product paths; disabled to allow scraping.
        "ROBOTSTXT_OBEY": False,
    }

    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q6711261",
                "name": "Líder",
            }
        }
    }

    sitemap_urls = [
        "https://www.lider.cl/siteindex.xml",
        "https://www.lider.cl/landing/static/sitemaps/sitemap.xml",
    ]
    sitemap_rules = [
        (r"/product/sku/(\d+)", "parse_sd"),
        (r"/ip/(?:.*/)?(\d+)$", "parse_sd"),
    ]

    convert_microdata = True
