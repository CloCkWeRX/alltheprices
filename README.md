A proof of concept repository to use the same style of scraping approach as [alltheplaces.xyz](https://alltheplaces.xyz/); in the Product domain.

The intended result is a dataset compatible with [Open Prices](https://github.com/openfoodfacts/open-prices) and or [ONDC](https://ondc.org/) services (a particular focus on grocery/supermarkets/food supply)

Borrows liberally from the codebase of https://alltheplaces.xyz/


# Roadmap

- [x] Schema.org Product/Offer spider, based on the structureddataspider
- [ ] ONDC spider
- [ ] Evaluate Common Crawl?
- [ ] Get running weekly somewhere
- [ ] CI infrastructure
- [ ] S3 infrastructure
- [ ] Static website/way to browse

# Dev setup

```
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
```

```
uv sync
```

```
uv run scrapy
```

# Scope/Priority

The main focus on this project is to reward publishers of structured/open data.

Following the ideas of https://5stardata.info/en/ prefer:

- Interlinked, rich data such as JSON-LD or Schema.org data (5 stars)
- Structured data such as Schema.org data (4 stars)
- Non-proprietary open format formats (JSON APIs, CSV, XML, etc) (3 stars)

Avoid unless the maintenance hassle is worth it

- Properietary formats (HTML with no structured data, Excel, etc) (2 stars or below)

