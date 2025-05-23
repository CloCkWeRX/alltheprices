# Scrapy settings for products project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#     http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
#     http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html

import os

import scrapy

import products

BOT_NAME = "products"

SPIDER_MODULES = ["products.spiders"]
NEWSPIDER_MODULE = "products.spiders"
COMMANDS_MODULE = "products.commands"


# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = f"Mozilla/5.0 (X11; Linux x86_64) {BOT_NAME}/{products.__version__} (+https://github.com/CloCkWeRX/alltheprices; framework {scrapy.__version__})"

ROBOTSTXT_USER_AGENT = BOT_NAME

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

FEED_URI = os.environ.get("FEED_URI")
FEED_FORMAT = os.environ.get("FEED_FORMAT")
FEED_EXPORTERS = {
    # "osm": "products.exporters.osm.OSMExporter",
}

# Configure maximum concurrent requests performed by Scrapy (default: 16)
# CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See http://scrapy.readthedocs.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY = 1
# The download delay setting will honor only one of:
# CONCURRENT_REQUESTS_PER_DOMAIN = 16
# CONCURRENT_REQUESTS_PER_IP = 16

# Set a timeout for requests
DOWNLOAD_TIMEOUT = 15

# Disable cookies (enabled by default)
# COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
TELNETCONSOLE_ENABLED = False

# Override the default request headers:
# DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
# }

# Enable or disable spider middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html
SPIDER_MIDDLEWARES = {
    "products.middlewares.track_sources.TrackSourcesMiddleware": 500,
}

# Enable or disable downloader middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {}

if os.environ.get("ZYTE_API_KEY"):
    DOWNLOAD_HANDLERS = {
        "http": "scrapy_zyte_api.ScrapyZyteAPIDownloadHandler",
        "https": "scrapy_zyte_api.ScrapyZyteAPIDownloadHandler",
    }
    DOWNLOADER_MIDDLEWARES = {
        "products.middlewares.zyte_api_by_country.ZyteApiByCountryMiddleware": 500,
        "scrapy_zyte_api.ScrapyZyteAPIDownloaderMiddleware": 1000,
    }
    REQUEST_FINGERPRINTER_CLASS = "scrapy_zyte_api.ScrapyZyteAPIRequestFingerprinter"
    TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

DOWNLOADER_MIDDLEWARES["products.middlewares.cdnstats.CDNStatsMiddleware"] = 500

# Enable or disable extensions
# See http://scrapy.readthedocs.org/en/latest/topics/extensions.html
# EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
# }

EXTENSIONS = {
    # "products.extensions.add_lineage.AddLineageExtension": 100,
    # "products.extensions.log_stats.LogStatsExtension": 1000,
}

# Configure item pipelines
# See http://scrapy.readthedocs.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    "products.pipelines.apply_spider_level_attributes.ApplySpiderLevelAttributesPipeline": 100,
    "products.pipelines.duplicates.DuplicatesPipeline": 200,
}

LOG_FORMATTER = "products.logformatter.DebugDuplicateLogFormatter"

# Enable and configure the AutoThrottle extension (disabled by default)
# See http://doc.scrapy.org/en/latest/topics/autothrottle.html
# AUTOTHROTTLE_ENABLED = True
# The initial download delay
# AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
# AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
# AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
# AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
# HTTPCACHE_ENABLED = True
# HTTPCACHE_EXPIRATION_SECS = 0
# HTTPCACHE_DIR = 'httpcache'
# HTTPCACHE_IGNORE_HTTP_CODES = []
# HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'

DEFAULT_PLAYWRIGHT_SETTINGS = {
    "PLAYWRIGHT_BROWSER_TYPE": "firefox",
    "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 30 * 1000,
    "PLAYWRIGHT_ABORT_REQUEST": lambda request: not request.resource_type == "document",
    "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
    "DOWNLOAD_HANDLERS": {
        "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    },
    "DOWNLOADER_MIDDLEWARES": {"products.middlewares.playwright_middleware.PlaywrightMiddleware": 543},
}

DEFAULT_PLAYWRIGHT_SETTINGS_WITH_EXT_JS = DEFAULT_PLAYWRIGHT_SETTINGS | {
    "PLAYWRIGHT_ABORT_REQUEST": lambda request: not request.resource_type == "document"
    and not request.resource_type == "script",
}

REQUESTS_CACHE_ENABLED = True
REQUESTS_CACHE_BACKEND_SETTINGS = {
    "expire_after": 60 * 60 * 24 * 3,
    "backend": "filesystem",
    "wal": True,
}

TEMPLATES_DIR = "templates/"
