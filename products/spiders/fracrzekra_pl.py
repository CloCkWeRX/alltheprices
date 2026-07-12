from scrapy.spiders import Rule, CrawlSpider
from scrapy.linkextractors import LinkExtractor
from products.structured_data_spider import StructuredDataSpider
from products.items import Product
from scrapy.http import Response

class FracrzekraPLSpider(CrawlSpider, StructuredDataSpider):
    """
    Spider for FRAC e-sklep RZESZÓW ul. Krakowska 20 (Poland).
    Wikidata: Q11698715
    Fixes #54.

    Sample output:
    {
        "name": "DOLNOŚLĄSKA MĄKA POZNAŃSKA 1 kg",
        "price": 2.99,
        "priceCurrency": "PLN",
        "website": "https://www.fracrzekra.pro-linuxpl.com/DOLNOSLASKA-MAKA-POZNANSKA-1-kg,p,101884",
        "image": "https://www.fracrzekra.pro-linuxpl.com/images/3000-4000/DOLNOSLASKA-MAKA-POZNANSKA-WOSEB_[3464]_1200.jpg",
        "ref": "101884",
        "located_in_wikidata": "Q11698715"
    }
    """
    name = "fracrzekra_pl"
    allowed_domains = ["fracrzekra.pro-linuxpl.com"]
    start_urls = ["https://www.fracrzekra.pro-linuxpl.com/"]

    item_attributes = {
        "located_in_wikidata": "Q11698715"
    }

    rules = (
        Rule(LinkExtractor(allow=r",c,\d+")),
        Rule(LinkExtractor(allow=r",p,(\d+)"), callback="parse_sd"),
    )

    def post_process_item(self, item: Product, response: Response, ld_data: dict, **kwargs):
        if not item.get("image"):
            item["image"] = response.css("#href_gallery_image::attr(data-src)").get() or response.css(".mainImage::attr(src)").get()

        if item.get("image") and item["image"].startswith("/"):
            item["image"] = response.urljoin(item["image"])

        item["located_in_wikidata"] = self.item_attributes["located_in_wikidata"]

        yield item
