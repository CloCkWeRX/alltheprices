from typing import Iterable

from scrapy import Request, Spider
from scrapy.http import Response

from products.items import Product
from products.user_agents import FIREFOX_LATEST


class TraderjoesUSSpider(Spider):
    """
    Spider for Trader Joe's (United States).
    Wikidata: Q688825
    Fixes #260.

    Sample output structured data:
    {
        "name": "Mandarin Crunch Pasta Salad",
        "website": "https://www.traderjoes.com/home/products/pdp/085000-side-mandarin-crunch-pasta-salad",
        "description": null,
        "image": "https://www.traderjoes.com/content/dam/trjo/products/m20501/85000.png",
        "ref": "085000",
        "brand": "Trader Joe's",
        "brand_wikidata": "Q688825",
        "located_in_wikidata": "Q688825",
        "price": 4.99,
        "proof_currency": "USD",
        "offers": [
            {
                "@type": "Offer",
                "priceCurrency": "USD",
                "price": 4.99,
                "availability": "https://schema.org/InStock"
            }
        ]
    }
    """

    name = "traderjoes_us"
    allowed_domains = ["traderjoes.com"]

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
        "brand": "Trader Joe's",
        "brand_wikidata": "Q688825",
        "located_in_wikidata": "Q688825",
    }

    graphql_url = "https://www.traderjoes.com/api/graphql"

    def start_requests(self) -> Iterable[Request]:
        yield Request(
            url="https://www.traderjoes.com/home/products/pdp/non-dairy-oat-creamer-gingerbread-079179",
            meta={"playwright": True, "playwright_include_page": True},
            callback=self.parse_start_page,
        )

    async def parse_start_page(self, response: Response):
        page = response.meta.get("playwright_page")
        if page:
            fetch_script = """async (params) => {
                const query = `query SearchProducts($search: String = "", $pageSize: Int = 100, $currentPage: Int = 1) {
                  products(search: $search, pageSize: $pageSize, currentPage: $currentPage) {
                    total_count
                    page_info {
                      current_page
                      total_pages
                    }
                    items {
                      sku
                      name
                      url_key
                      item_title
                      item_description
                      primary_image
                      primary_image_meta {
                        url
                      }
                      retail_price
                      price_range {
                        minimum_price {
                          final_price {
                            currency
                            value
                          }
                        }
                      }
                    }
                  }
                }`;
                const res = await fetch('https://www.traderjoes.com/api/graphql', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify({
                        operationName: 'SearchProducts',
                        variables: { search: '', pageSize: params.pageSize, currentPage: params.page },
                        query: query
                    })
                });
                return await res.json();
            }"""

            current_page = 1
            total_pages = 1

            while current_page <= total_pages:
                self.logger.info(
                    f"Fetching GraphQL page {current_page}/{total_pages}..."
                )
                try:
                    res_data = await page.evaluate(
                        fetch_script,
                        {"pageSize": 100, "page": current_page},
                    )
                except Exception as e:
                    self.logger.error(
                        f"Error evaluating fetch_script on page {current_page}: {e}"
                    )
                    break

                products_data = res_data.get("data", {}).get("products", {})
                items = products_data.get("items", [])
                page_info = products_data.get("page_info", {})
                total_pages = page_info.get("total_pages", total_pages)

                self.logger.info(
                    f"Page {current_page} returned {len(items)} items"
                )

                for item in items:
                    sku = item.get("sku")
                    if not sku:
                        continue

                    name = item.get("item_title") or item.get("name")
                    if not name:
                        continue
                    name = name.strip()

                    url_key = item.get("url_key")
                    if url_key:
                        website = (
                            f"https://www.traderjoes.com/home/products/pdp/{url_key}"
                        )
                    else:
                        website = (
                            f"https://www.traderjoes.com/home/products/pdp/{sku}"
                        )

                    description = item.get("item_description")
                    if description:
                        description = description.strip()

                    img_path = item.get("primary_image")
                    if not img_path and item.get("primary_image_meta"):
                        img_path = item.get("primary_image_meta", {}).get("url")

                    image = None
                    if img_path:
                        if img_path.startswith("http"):
                            image = img_path
                        else:
                            image = f"https://www.traderjoes.com{img_path}"

                    price = None
                    retail_price = item.get("retail_price")
                    if retail_price is not None:
                        try:
                            price = float(retail_price)
                        except (ValueError, TypeError):
                            pass

                    currency = "USD"
                    price_range = item.get("price_range") or {}
                    min_price = price_range.get("minimum_price") or {}
                    final_price = min_price.get("final_price") or {}
                    if price is None and final_price.get("value") is not None:
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
                        description=description,
                        image=image,
                        ref=str(sku),
                        price=price,
                        proof_currency=currency,
                        offers=offers,
                        **self.item_attributes,
                    )

                current_page += 1

            await page.close()
