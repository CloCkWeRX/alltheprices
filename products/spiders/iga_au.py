from scrapy.spiders import SitemapSpider
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST

class IgaAUSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for IGA Australia (igashop.com.au).
    IGA Australia is owned by Metcash.

    Sample output:
    {
        'brand': 'NIVEA',
        'extras': {
            'seller': {
                '@id': 'https://www.wikidata.org/wiki/Q23073728',
                '@type': 'Organization',
                'name': 'Metcash Limited'
            }
        },
        'image': 'https://cdn.metcash.media/image/upload/w_1500,h_1500,c_pad,b_auto/igashop/images/494526.jpg',
        'located_in': 'Australia',
        'located_in_wikidata': 'Q5970945',
        'name': ' NIVEA 3in1 Refreshing Cleansing Wipes',
        'offers': [{
            '@type': 'Offer',
            'availability': 'https://schema.org/InStock',
            'itemCondition': 'https://schema.org/NewCondition',
            'priceSpecification': {
                '@type': 'UnitPriceSpecification',
                'price': 5.95,
                'priceCurrency': 'AUD',
                'referenceQuantity': {
                    '@type': 'QuantitativeValue',
                    'unitCode': 'ct',
                    'value': 25,
                    'valueReference': {
                        '@type': 'QuantitativeValue',
                        'unitCode': 'ct',
                        'value': 1
                    }
                }
            },
            'url': 'https://www.igashop.com.au/product/nivea-3in1-refreshing-cleansing-wipes-494526'
        }],
        'price': 5.95,
        'proof_currency': 'AUD',
        'ref': '494526',
        'sku': '494526',
        'website': 'https://www.igashop.com.au/product/nivea-3in1-refreshing-cleansing-wipes-494526'
    }
    """
    name = "iga_au"
    allowed_domains = ["igashop.com.au"]
    sitemap_urls = ["https://www.igashop.com.au/sitemap_index.xml"]
    sitemap_rules = [
        (r"/product/.*", "parse_sd"),
    ]

    custom_settings = {
        "USER_AGENT": FIREFOX_LATEST,
        "ROBOTSTXT_OBEY": False,
    }

    def post_process_item(self, item, response, ld_data):
        if item.get("offers"):
            offer = item["offers"][0]
            price = offer.get("price")
            currency = offer.get("priceCurrency")

            if not price and "priceSpecification" in offer:
                spec = offer["priceSpecification"]
                if isinstance(spec, list):
                    spec = spec[0]
                price = spec.get("price")
                currency = spec.get("priceCurrency")

            item["price"] = price
            item["proof_currency"] = currency

        brand = ld_data.get("brand")
        if isinstance(brand, dict):
            item["brand"] = brand.get("name")
        elif isinstance(brand, str):
            item["brand"] = brand

        for gtin_key in ["gtin13", "gtin12", "gtin8", "gtin"]:
            if gtin := ld_data.get(gtin_key):
                item["gtin"] = gtin
                break

        item["located_in"] = "Australia"
        item["located_in_wikidata"] = "Q5970945"

        if "seller" not in item["extras"]:
            item["extras"]["seller"] = {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q23073728",
                "name": "Metcash Limited",
            }

        if item.get("name"):
            item["name"] = item["name"].strip()

        yield item
