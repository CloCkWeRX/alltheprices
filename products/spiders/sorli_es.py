import scrapy
from scrapy.spiders import SitemapSpider
from products.items import Product
from products.user_agents import FIREFOX_LATEST

class SorliESSpider(SitemapSpider):
    """
    Sorli (Spain) spider.
    Uses Playwright to render category pages and extract products from the DOM.
    Wikidata: Q20103935

    Sample output structured data:
    {
        "brand": "MARBU",
        "image": "https://cdn.sorliclic.com/imagenes/articulos/135x135/189732.png",
        "located_in_wikidata": "Q20103935",
        "name": "Galleta Dorada 600 Gr",
        "price": 3.49,
        "proof_currency": "EUR",
        "ref": "189732",
        "website": "https://www.sorliclic.com/es/p/189732"
    }
    """
    name = "sorli_es"
    allowed_domains = ["sorliclic.com"]
    sitemap_urls = ["https://www.sorliclic.com/sitemap.xml"]
    sitemap_rules = [(r"/es/c/\d+/", "parse_category")]

    custom_settings = {
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "DOWNLOAD_HANDLERS": {
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "PLAYWRIGHT_BROWSER_TYPE": "firefox",
        "PLAYWRIGHT_LAUNCH_OPTIONS": {"headless": True},
        "USER_AGENT": FIREFOX_LATEST,
        "ROBOTSTXT_OBEY": False,
        "CONCURRENT_REQUESTS": 1,
    }

    def parse_category(self, response):
        yield scrapy.Request(
            response.url,
            callback=self.parse_products,
            meta={
                "playwright": True,
                "playwright_include_page": True,
            },
            dont_filter=True
        )

    async def parse_products(self, response):
        page = response.meta["playwright_page"]

        try:
            # Click accept cookies to clear the overlay
            try:
                await page.click("button:has-text('Permetre totes les cookies')", timeout=5000)
            except:
                pass

            # Wait for products to load
            await page.wait_for_selector(".contenedor-producto", timeout=30000)

            products_data = await page.evaluate('''() => {
                let items = document.querySelectorAll('.contenedor-producto');
                return Array.from(items).map(item => {
                    let brand = item.querySelector('.informacion-marca')?.innerText.trim();
                    let name = item.querySelector('.descripcion-producto')?.innerText.trim();
                    let priceFinal = item.querySelector('.precio-final')?.innerText.trim();
                    let img = item.querySelector('img.img-product-grid')?.src;

                    let ref = null;
                    if (img) {
                        let parts = img.split('/');
                        let filename = parts[parts.length - 1];
                        ref = filename.split('.')[0];
                    }

                    return {
                        brand,
                        name,
                        price: priceFinal,
                        image: img,
                        ref: ref
                    };
                });
            }''')

            for data in products_data:
                if not data["name"]:
                    continue

                product = Product()
                product["name"] = data["name"]
                product["brand"] = data["brand"]
                product["image"] = data["image"]
                product["ref"] = data["ref"]

                if data["ref"]:
                    product["website"] = f"https://www.sorliclic.com/es/p/{data['ref']}"
                else:
                    product["website"] = response.url

                if data["price"]:
                    price_text = data["price"].replace("€", "").replace(",", ".").strip()
                    try:
                        product["price"] = float(price_text)
                        product["proof_currency"] = "EUR"
                    except ValueError:
                        pass

                product["located_in_wikidata"] = "Q20103935"
                yield product

        except Exception as e:
            self.logger.error(f"Error parsing category {response.url}: {e}")
        finally:
            await page.close()
