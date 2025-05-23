FROM python:3.11-bookworm

# install uv to manage python
COPY --from=ghcr.io/astral-sh/uv:0.6.11 /uv /uvx /bin/

# install some dependencies that are useful for the build
RUN apt-get update \
 && apt-get install -qq -y \
    jq \
    git \
    curl \
 && rm -rf /var/lib/apt/lists/*

# install dependencies from uv
COPY pyproject.toml pyproject.toml
COPY uv.lock uv.lock
RUN uv sync --frozen

RUN uv run playwright install-deps \
 && uv run playwright install firefox

COPY . .

ARG GIT_COMMIT
ENV GIT_COMMIT=$GIT_COMMIT

# CMD ["/home/ubuntu/ci/run_all_spiders.sh"]
