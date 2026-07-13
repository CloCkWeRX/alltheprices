import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class SilpoUASpider(CrawlSpider, StructuredDataSpider):
    """
    Spider for Silpo (Ukraine).
    Wikidata: Q4419434

    Sample output:
    {
        "name": "Йогурт «На здоров'я» «Гρεцький» 10% 280г",
        "website": "https://silpo.ua/product/yogurt-na-zdorov-ia-gretskyi-10-917589",
        "image": "https://images.silpo.ua/v2/products/500x500/origin/dbfafde1-2019-4cc3-b616-20877ff8fcaf.png",
        "ref": "917589",
        "offers": [
            {
                "@type": "Offer",
                "price": "53.49",
                "priceCurrency": "UAH",
                "availability": "https://schema.org/InStock",
                "seller": {
                    "@type": "Organization",
                    "name": "Сільпо"
                }
            }
        ],
        "located_in_wikidata": "Q4419434",
        "proof_currency": "UAH",
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q4419434",
                "name": "Сільпо"
            }
        }
    }

    @url https://silpo.ua/product/vershky-galychyna-ultrapasteryzovani-10-815587
    @returns items 1
    @scrapes name website image ref offers
    """

    name = "silpo_ua"
    allowed_domains = ["silpo.ua"]
    start_urls = ["https://silpo.ua/"]

    item_attributes = {
        "located_in_wikidata": "Q4419434",
        "proof_currency": "UAH",
        "extras": {
            "seller": {
                "@type": "Organization",
                "@id": "https://www.wikidata.org/wiki/Q4419434",
                "name": "Сільпо",
            }
        },
    }

    def use_playwright(self, request, response):
        request.meta["playwright"] = True
        return request

    rules = (
        Rule(
            LinkExtractor(allow=r"/product/.*-(\d+)$"),
            callback="parse_sd",
            process_request="use_playwright",
        ),
        Rule(LinkExtractor(allow=r"/category/"), follow=True, process_request="use_playwright"),
    )

    custom_settings = {
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "DOWNLOAD_HANDLERS": {
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "PLAYWRIGHT_BROWSER_TYPE": "firefox",
        "PLAYWRIGHT_LAUNCH_OPTIONS": {
            "headless": True,
        },
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": FIREFOX_LATEST,
    }

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url, meta={"playwright": True})
