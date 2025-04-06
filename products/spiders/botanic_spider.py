import scrapy


class BotanicSpiderSpider(scrapy.Spider):
    name = "botanic_spider"
    allowed_domains = ["botanic.com"]
    start_urls = ["https://botanic.com"]

    def parse(self, response):
        pass
