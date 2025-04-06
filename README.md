A proof of concept repository to use the same style of scraping approach as [alltheplaces.xyz](https://alltheplaces.xyz/); in the Product domain.

The intended result is a dataset compatible with [Open Prices](https://github.com/openfoodfacts/open-prices) and or [ONDC](https://ondc.org/) services.

Borrows liberally from the codebase of https://alltheplaces.xyz/


# Roadmap

- [ ] Schema.org Product/Offer spider, based on the structureddataspider
- [ ] ONDC spider
- [ ] Evaluate Common Crawl?

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