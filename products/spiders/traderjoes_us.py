import scrapy
from scrapy import Request
from products.items import Product
from products.user_agents import FIREFOX_LATEST


class TraderjoesUSSpider(scrapy.Spider):
    """
    Spider for Trader Joe's (United States) (Q688825).
    Fix #260.
    """

    name = "traderjoes_us"
    allowed_domains = ["traderjoes.com"]
    start_urls = [
        "https://www.traderjoes.com/home/products/pdp/non-dairy-oat-creamer-gingerbread-079179"
    ]

    custom_settings = {
        "TWISTED_REACTOR": (
            "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
        ),
        "DOWNLOAD_HANDLERS": {
            "https": (
                "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler"
            ),
            "http": (
                "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler"
            ),
        },
        "PLAYWRIGHT_BROWSER_TYPE": "firefox",
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 60 * 1000,
        "PLAYWRIGHT_LAUNCH_OPTIONS": {
            "headless": True,
        },
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": FIREFOX_LATEST,
        "CONCURRENT_REQUESTS": 1,
    }

    item_attributes = {
        "located_in_wikidata": "Q688825",
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q688825",
                "name": "Trader Joe's",
            }
        },
    }

    GRAPHQL_QUERY = """
    query SearchProducts($search: String, $pageSize: Int = 100, $currentPage: Int = 1, $storeCode: String = "TJ", $published: String = "1") {
      products(
        search: $search
        pageSize: $pageSize
        currentPage: $currentPage
        filter: {store_code: {eq: $storeCode}, published: {eq: $published}}
      ) {
        total_count
        page_info {
          total_pages
          current_page
        }
        items {
          sku
          name
          item_title
          url_key
          retail_price
          primary_image
          item_description
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
    }
    """

    def start_requests(self):
        for url in self.start_urls:
            yield Request(
                url,
                callback=self.parse_api,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_context_kwargs": {
                        "user_agent": FIREFOX_LATEST,
                    },
                },
            )

    async def parse_api(self, response):
        page = response.meta.get("playwright_page")
        if not page:
            self.logger.error("Playwright page unavailable")
            return

        try:
            current_page = 1
            total_pages = 1

            while current_page <= total_pages:
                gql_res = await page.evaluate(
                    """
                    async (args) => {
                        try {
                            const res = await fetch("https://www.traderjoes.com/api/graphql", {
                                method: "POST",
                                headers: {
                                    "content-type": "application/json",
                                    "accept": "*/*"
                                },
                                body: JSON.stringify({
                                    operationName: "SearchProducts",
                                    variables: {
                                        storeCode: "TJ",
                                        published: "1",
                                        pageSize: 100,
                                        currentPage: args.currentPage
                                    },
                                    query: args.query
                                })
                            });
                            if (res.ok) {
                                return await res.json();
                            }
                        } catch (e) {
                            console.log("Fetch error:", e);
                        }
                        return null;
                    }
                    """,
                    {"currentPage": current_page, "query": self.GRAPHQL_QUERY},
                )

                if not gql_res or "data" not in gql_res:
                    self.logger.warning(
                        f"Failed to fetch page {current_page}"
                    )
                    break

                products_data = gql_res["data"]["products"]
                items = products_data.get("items") or []
                page_info = products_data.get("page_info") or {}
                total_pages = page_info.get("total_pages", total_pages)

                self.logger.info(
                    f"Fetched page {current_page}/{total_pages} with {len(items)} items"
                )

                for item_data in items:
                    sku = item_data.get("sku")
                    item_title = item_data.get("item_title") or item_data.get(
                        "name"
                    )
                    if not sku or not item_title:
                        continue

                    url_key = item_data.get("url_key") or f"{sku}"
                    pdp_url = f"https://www.traderjoes.com/home/products/pdp/{url_key}"

                    product = Product()
                    product["name"] = item_title.strip()
                    product["ref"] = sku
                    product["sku"] = sku
                    product["website"] = pdp_url

                    # Price extraction
                    price_val = None
                    currency = "USD"
                    price_range = item_data.get("price_range") or {}
                    min_price = price_range.get("minimum_price") or {}
                    final_price = min_price.get("final_price") or {}
                    if final_price.get("value") is not None:
                        price_val = float(final_price["value"])
                        if final_price.get("currency"):
                            currency = final_price["currency"]
                    elif item_data.get("retail_price") is not None:
                        try:
                            price_val = float(item_data["retail_price"])
                        except (ValueError, TypeError):
                            pass

                    if price_val is not None:
                        product["price"] = price_val
                        product["proof_currency"] = currency

                    # Image URL
                    primary_image = item_data.get("primary_image")
                    if primary_image:
                        if not primary_image.startswith("http"):
                            primary_image = f"https://www.traderjoes.com{primary_image}"
                        product["image"] = primary_image

                    # Description
                    desc = item_data.get("item_description")
                    if desc:
                        product["description"] = desc.strip()

                    product["brand"] = "Trader Joe's"
                    product["brand_wikidata"] = "Q688825"
                    product["located_in_wikidata"] = "Q688825"
                    product["extras"] = {
                        "seller": {
                            "@type": "Organization",
                            "@id": "https://www.wikidata.org/wiki/Q688825",
                            "name": "Trader Joe's",
                        }
                    }

                    yield product

                current_page += 1
        finally:
            await page.close()
