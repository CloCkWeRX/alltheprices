from scrapy.spiders import SitemapSpider
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST

class ThesourcebulkfoodsAUSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for The Source Bulk Foods (Australia).

    Sample output:
    {
        'extras': {'@source_uri': 'https://shop.thesourcebulkfoods.com.au/product/yoshino/'},
        'image': 'https://shop.thesourcebulkfoods.com.au/wp-content/uploads/sites/3/2019/10/Yoshino.jpg',
        'located_in': 'Australia',
        'located_in_wikidata': 'Q120732890',
        'name': 'Yoshino',
        'offers': [{'@type': 'Offer',
                    'availability': 'http://schema.org/InStock',
                    'price': '38.50',
                    'priceCurrency': 'AUD',
                    'priceSpecification': {'price': '38.50',
                                            'priceCurrency': 'AUD',
                                            'valueAddedTaxIncluded': 'true'},
                    'priceValidUntil': '2027-12-31',
                    'seller': {'@type': 'Organization',
                                'name': 'The Source Bulk Foods Shop',
                                'url': 'https://shop.thesourcebulkfoods.com.au'},
                    'url': 'https://shop.thesourcebulkfoods.com.au/product/yoshino/'}],
        'price': '38.50',
        'proof_currency': 'AUD',
        'ref': '30124',
        'website': 'https://shop.thesourcebulkfoods.com.au/product/yoshino/'
    }
    """
    name = "thesourcebulkfoods_au"
    allowed_domains = ["thesourcebulkfoods.com.au", "shop.thesourcebulkfoods.com.au"]
    sitemap_urls = ["https://thesourcebulkfoods.com.au/au-sitemap.xml"]
    sitemap_rules = [
        (r"/shop/.*", "parse_sd"),
    ]

    custom_settings = {
        "USER_AGENT": FIREFOX_LATEST,
        "ROBOTSTXT_OBEY": False,
    }

    def post_process_item(self, item, response, ld_data):
        # StructuredDataSpider puts the offers list in item["offers"]
        if item.get("offers"):
            offer = item["offers"][0]
            item["price"] = offer.get("price")
            item["proof_currency"] = offer.get("priceCurrency")

        item["located_in"] = "Australia"
        item["located_in_wikidata"] = "Q120732890"
        yield item
