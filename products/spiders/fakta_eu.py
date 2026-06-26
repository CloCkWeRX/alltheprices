import re
from scrapy.spiders import SitemapSpider
from products.structured_data_spider import StructuredDataSpider
from products.items import Product
from scrapy.http import Response


class FaktaEUSpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for Fakta (EU).
    Wikidata: Q1394332

    Sample output structured data:
    {
        "name": "Krydderihaven Ras el hanout 150 g",
        "website": "https://www.fakta.eu/pi/Krydderihaven-Ras-el-hanout-150-g_22338183_162157.aspx",
        "image": "https://www.fakta.eu/Services/ImageHandler.ashx?imgId=2539633&sizeId=0&RevisionNo=0_0",
        "ref": "5712426000049",
        "sku": "5712426000049",
        "offers": [
            {
                "@type": "Offer",
                "url": "https://www.fakta.eu/pi/Krydderihaven-Ras-el-hanout-150-g_22338183_162157.aspx",
                "priceCurrency": "DKK",
                "price": 24.99,
                "availability": "https://schema.org/InStock"
            }
        ],
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q1394332",
                "name": "Fakta"
            }
        }
    }
    """

    name = "fakta_eu"
    allowed_domains = ["fakta.eu"]
    sitemap_urls = ["https://www.fakta.eu/googlesitemap.ashx"]
    sitemap_rules = [
        (r"/pi/.*_(\d+)_(\d+)\.aspx$", "parse_sd"),
    ]

    json_parser = "chompjs"

    item_attributes = {
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q1394332",
                "name": "Fakta",
            }
        }
    }

    def post_process_item(self, item: Product, response: Response, ld_data: dict, **kwargs):
        # Handle the dynamic price variable 'tagPrice'
        for offer in item.get("offers", []):
            if offer.get("price") == "tagPrice":
                # Try to extract tagPrice from the page source
                # Example: var tagPrice = Number(14,9899938000.replace(',','.')).toFixed(2);
                match = re.search(r"var tagPrice = Number\(([^)]+)\)", response.text)
                if match:
                    price_expr = match.group(1)
                    # Split by comma to handle the comma operator in JS
                    parts = price_expr.split(",")
                    if len(parts) > 1:
                        # Find the first part that looks like it has a numeric value
                        # In "14,9899938000.replace(',','.')", parts are ["14", "9899938000.replace('", "'", "'.')"]
                        # This is tricky because .replace(',','.') also contains commas.
                        # Re-join parts that belong to the replace call.
                        # Actually, just take the first part and the start of the second part.
                        price_str = parts[0] + "." + re.sub(r"[^\d]", "", parts[1])
                    else:
                        price_str = re.sub(r"[^\d.]", "", price_expr)

                    try:
                        offer["price"] = round(float(price_str), 2)
                    except ValueError:
                        pass

        if not item.get("ref") and item.get("sku"):
            item["ref"] = item["sku"]

        yield item
