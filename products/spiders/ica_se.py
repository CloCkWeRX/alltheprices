import re
from scrapy import Request
from scrapy.spiders import SitemapSpider
from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class IcaSESpider(SitemapSpider, StructuredDataSpider):
    """
    Spider for ICA Sweden (handla.ica.se).
    Wikidata: Q1663776
    Fix #467

    Sample output:
    {
        "name": "Baguetter 2-p 300g ICA",
        "website": "https://handla.ica.se/produkt/2084605",
        "image": "https://assets.icanet.se/image/upload/cs_srgb/t_product_large_2x_v1/irvyy14sbx27vg4o4bly.webp",
        "ref": "2084605",
        "sku": "7318690498490",
        "brand": "ICA",
        "brand_wikidata": "Q1663776",
        "proof_currency": "SEK",
        "located_in_wikidata": "Q1663776"
    }
    """

    name = "ica_se"
    allowed_domains = ["handla.ica.se"]
    sitemap_urls = ["https://handla.ica.se/sitemap"]
    sitemap_rules = [(r"/produkt/(\d+)", "parse_sd")]

    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": FIREFOX_LATEST,
        "CONCURRENT_REQUESTS": 4,
        "DOWNLOAD_DELAY": 0.5,
    }

    item_attributes = {
        "located_in_wikidata": "Q1663776",
    }

    convert_microdata = True

    def sitemap_filter(self, entries):
        for entry in entries:
            # We want to crawl all nested sitemaps (like handla.ica.se/sitemap/category/...)
            # but avoid full sitemap crawls of non-category/product things if any.
            yield entry

    def post_process_item(self, item, response, ld_data):
        item["located_in_wikidata"] = "Q1663776"
        item["proof_currency"] = "SEK"

        # Capture unique ref as the product ID from the URL (e.g. 2084605)
        # and store EAN/GTIN/SKU from ld_data as the sku/gtin.
        url_match = re.search(r"/produkt/(\d+)", response.url)
        if url_match:
            product_id = url_match.group(1)
            # Use product ID from the URL as 'ref' since that's the canonical unique ID of the page.
            # If the spider sets 'ref' to SKU (EAN), we can overwrite it with product_id or keep EAN as sku/gtin.
            sku_val = item.get("ref") or item.get("sku")
            item["ref"] = product_id
            if sku_val:
                item["sku"] = sku_val
                # If sku_val looks like a valid EAN-13, we can set gtin/gtin13 as well
                if re.match(r"^\d{13}$", str(sku_val)):
                    item["gtin13"] = str(sku_val)
                    item["gtin"] = str(sku_val)

        # Ensure brand name is set and check if it's the own brand 'ICA'
        brand = item.get("brand") or ld_data.get("brand")
        if brand:
            if isinstance(brand, dict):
                brand_name = brand.get("name")
            else:
                brand_name = brand

            if brand_name:
                item["brand"] = brand_name
                if brand_name.lower().strip() == "ica":
                    item["brand_wikidata"] = "Q1663776"

        yield item
