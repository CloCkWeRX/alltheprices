from scrapy.spiders import SitemapSpider

from products.structured_data_spider import StructuredDataSpider

class BotanicSpider(SitemapSpider, StructuredDataSpider):
    name = "botanic"
    allowed_domains = ["botanic.com"]

    sitemap_urls = ["https://www.botanic.com/Assets/Rbs/Seo/100541/fr_FR/Rbs_Catalog_Product.1.xml"]
    sitemap_rules = [
        (r"https://www.botanic.com/produit/\d+/[\w]+.html", "parse_sd"),
    ]
