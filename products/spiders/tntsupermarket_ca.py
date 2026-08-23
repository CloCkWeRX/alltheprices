from typing import Iterable

from scrapy import Request, Spider
from scrapy.http import Response

from products.items import Product
from products.user_agents import FIREFOX_LATEST


class TntsupermarketCASpider(Spider):
    """
    Spider for T&T Supermarket (Canada).
    Wikidata: Q837893
    Fixes #303.

    Sample output structured data:
    {
        "name": "Want Want Black Truffle Egg Yolk Rice Cracker (56g)",
        "website": "https://www.tntsupermarket.com/eng/54021001-want-want-blk-truffle-egg-yolk-rice-crk.html",
        "description": null,
        "image": "https://www.tntsupermarket.com/media/catalog/product/cache/bcdaf6b1995582a96f9153e74ec2458b/5/4/5402100101774376411.jpg",
        "ref": "54021001",
        "brand": "T&T Supermarket",
        "brand_wikidata": "Q837893",
        "located_in_wikidata": "Q837893",
        "price": 2.29,
        "proof_currency": "CAD",
        "offers": [
            {
                "@type": "Offer",
                "priceCurrency": "CAD",
                "price": 2.29,
                "availability": "https://schema.org/InStock"
            }
        ]
    }
    """

    name = "tntsupermarket_ca"
    allowed_domains = ["tntsupermarket.com"]

    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": FIREFOX_LATEST,
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "PLAYWRIGHT_BROWSER_TYPE": "firefox",
        "PLAYWRIGHT_LAUNCH_OPTIONS": {"headless": True},
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 30 * 1000,
    }

    item_attributes = {
        "brand": "T&T Supermarket",
        "brand_wikidata": "Q837893",
        "located_in_wikidata": "Q837893",
    }

    search_terms = ["sauce", "rice", "noodle", "snack", "tea", "drink", "soup", "oil", "sweet", "fresh", "frozen"]

    def start_requests(self) -> Iterable[Request]:
        yield Request(
            url="https://www.tntsupermarket.com/eng/",
            meta={"playwright": True, "playwright_include_page": True},
            callback=self.parse_start_page,
        )

    async def parse_start_page(self, response: Response):
        page = response.meta.get("playwright_page")
        if not page:
            return

        fetch_script = """async (params) => {
            const query = `query SearchProducts($search: String!, $currentPage: Int!, $pageSize: Int!) {
              products(search: $search, currentPage: $currentPage, pageSize: $pageSize) {
                total_count
                page_info {
                  current_page
                  total_pages
                }
                items {
                  id
                  sku
                  name
                  url_key
                  small_image {
                    url
                  }
                  price_range {
                    minimum_price {
                      final_price {
                        value
                        currency
                      }
                      regular_price {
                        value
                        currency
                      }
                    }
                  }
                }
              }
            }`;
            const res = await fetch("https://www.tntsupermarket.com/graphql", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Store": "eng"
                },
                body: JSON.stringify({
                    operationName: "SearchProducts",
                    variables: { search: params.search, currentPage: params.page, pageSize: params.pageSize },
                    query: query
                })
            });
            return await res.json();
        }"""

        seen_skus = set()

        try:
            for term in self.search_terms:
                current_page = 1
                total_pages = 1

                while current_page <= total_pages:
                    self.logger.info(f"Fetching term '{term}' page {current_page}/{total_pages}...")
                    try:
                        res_data = await page.evaluate(
                            fetch_script,
                            {"search": term, "page": current_page, "pageSize": 100},
                        )
                    except Exception as e:
                        self.logger.error(f"Error evaluating fetch_script for term '{term}' page {current_page}: {e}")
                        break

                    products_data = res_data.get("data", {}).get("products", {})
                    items = products_data.get("items", [])
                    page_info = products_data.get("page_info", {})
                    total_pages = page_info.get("total_pages", total_pages)

                    if not items:
                        break

                    self.logger.info(f"Term '{term}' page {current_page} returned {len(items)} items")

                    for item in items:
                        sku = item.get("sku")
                        if not sku or sku in seen_skus:
                            continue
                        seen_skus.add(sku)

                        name = item.get("name")
                        if not name:
                            continue
                        name = name.strip()

                        url_key = item.get("url_key")
                        if url_key:
                            website = f"https://www.tntsupermarket.com/eng/{url_key}.html"
                        else:
                            website = f"https://www.tntsupermarket.com/eng/{sku}.html"

                        image = None
                        small_img = item.get("small_image")
                        if small_img and small_img.get("url"):
                            image = small_img.get("url")

                        price = None
                        currency = "CAD"
                        price_range = item.get("price_range") or {}
                        min_price = price_range.get("minimum_price") or {}
                        final_price = min_price.get("final_price") or {}
                        if final_price.get("value") is not None:
                            try:
                                price = float(final_price.get("value"))
                            except (ValueError, TypeError):
                                pass
                        if final_price.get("currency"):
                            currency = final_price.get("currency")

                        offers = []
                        if price is not None:
                            offers.append({
                                "@type": "Offer",
                                "priceCurrency": currency,
                                "price": price,
                                "availability": "https://schema.org/InStock",
                            })

                        yield Product(
                            name=name,
                            website=website,
                            image=image,
                            ref=str(sku),
                            price=price,
                            proof_currency=currency,
                            offers=offers,
                            **self.item_attributes,
                        )

                    current_page += 1
        finally:
            await page.close()
