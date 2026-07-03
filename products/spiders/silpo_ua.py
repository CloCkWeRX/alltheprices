import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from products.structured_data_spider import StructuredDataSpider
from products.user_agents import FIREFOX_LATEST


class SilpoUASpider(CrawlSpider, StructuredDataSpider):
    """
    Spider for Silpo (Ukraine).
    Wikidata: Q4419434

    @url https://silpo.ua/product/vershky-galychyna-ultrapasteryzovani-10-815587
    @returns items 1
    @scrapes name website image ref offers
    """

    name = "silpo_ua"
    allowed_domains = ["silpo.ua"]
    start_urls = [
        "https://silpo.ua/category/frukty-ovochi-4788",
        "https://silpo.ua/category/m-iaso-4411",
        "https://silpo.ua/category/ryba-ikra-4458",
        "https://silpo.ua/category/molochni-produkty-ta-iaitsia-234",
        "https://silpo.ua/category/khlib-vypichka-kondyterski-vyroby-278",
        "https://silpo.ua/category/bakaliia-293",
        "https://silpo.ua/category/napoi-209",
        "https://silpo.ua/category/alkogol-355",
        "https://silpo.ua/category/soloshchi-sneky-311",
        "https://silpo.ua/category/zamorozheni-produkty-336",
        "https://silpo.ua/category/dytiachi-tovary-391",
        "https://silpo.ua/category/tovary-dlia-tila-ta-zdorov-ia-375",
        "https://silpo.ua/category/tovary-dlia-domu-hospodarchi-tovary-413",
        "https://silpo.ua/category/tovary-dlia-tvaryn-444",
    ]

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
