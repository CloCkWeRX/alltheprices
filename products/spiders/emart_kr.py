from scrapy.spiders import SitemapSpider
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST

class EmartKRSpider(SitemapSpider, StructuredDataSpider):
    name = "emart_kr"
    allowed_domains = ["emart.ssg.com", "ssg.com"]
    sitemap_urls = ["https://emart.ssg.com/sitemap/emart-sitemap.xml"]
    sitemap_rules = [(r"itemId=(\d+)", "parse")]

    custom_settings = {
        "USER_AGENT": FIREFOX_LATEST,
        "ROBOTSTXT_OBEY": False,
    }

    located_in_wikidata = "Q490333"

    def post_process_item(self, item, response, ld_data):
        # Prepend https:// to image URLs if they start with sitem.ssgcdn.com
        images = item.get("image")
        if images:
            new_images = []
            if isinstance(images, str):
                images = [images]
            for img in images:
                if img.startswith("sitem.ssgcdn.com"):
                    new_images.append("https://" + img)
                else:
                    new_images.append(img)
            item["image"] = new_images

        # Ensure the currency is set to KRW
        item["proof_currency"] = "KRW"

        yield item
