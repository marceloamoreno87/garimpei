# Bases resolved from the official registries; see F23/runtime-lock.json.
FROM ghcr.io/astral-sh/uv:0.11.24@sha256:99ea34acedc870ba4ad11a1f540a1c04267c9f30aadc465a94406f52dfda2c36 AS uv
FROM docker:29.9.3-cli@sha256:5a7af0dcb0e46c803efe9b45371dd21cb500e5b4453250394ac6f06d49b6e6f1 AS docker
FROM node:22.22.0-bookworm-slim@sha256:dd9d21971ec4395903fa6143c2b9267d048ae01ca6d3ea96f16cb30df6187d94 AS node
FROM python:3.13.14-slim-bookworm@sha256:67a1e1f215ccda113cfc024e8639049257e88f273898f595b61476d128d387e8 AS runtime
COPY --from=uv /uv /uvx /usr/local/bin/
ENV UV_PYTHON_DOWNLOADS=never UV_LINK_MODE=copy PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 \
    PATH=/app/apps/backend/.venv/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
WORKDIR /app/apps/backend
COPY apps/backend/pyproject.toml apps/backend/uv.lock apps/backend/.python-version ./
RUN apt-get update && apt-get install -y --no-install-recommends libatomic1 postgresql-client git && \
    uv sync --frozen --no-dev --no-install-project && uv run --no-sync playwright install --with-deps chromium && \
    rm -rf /var/lib/apt/lists/* && useradd --create-home --uid 1000 garimpei
COPY apps/backend/src ./src
COPY apps/backend/manage.py ./manage.py
COPY docs/F19-inferencia-multimodal-local-em-docker/model-lock.json /app/docs/F19-inferencia-multimodal-local-em-docker/model-lock.json
COPY docs/F18-identificacao-de-produtos-e-busca-ativa-de-comparaveis/evidence /app/docs/F18-identificacao-de-produtos-e-busca-ativa-de-comparaveis/evidence
RUN uv sync --frozen --no-dev && \
    python -m garimpei.infra.runtime.container_artifacts build-tokenizer && \
    chmod 755 /app/artifacts && chmod 644 /app/artifacts/tokenizer.json
USER garimpei
ENTRYPOINT ["python", "-m", "garimpei.infra.runtime.container_entrypoint"]
CMD ["web"]
FROM runtime AS quality
USER root
COPY --from=docker /usr/local/bin/docker /usr/local/bin/docker
COPY --from=docker /usr/local/libexec/docker/cli-plugins/docker-compose /usr/local/libexec/docker/cli-plugins/docker-compose
COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s ../lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm && \
    ln -s ../lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx && \
    npm install --global @playwright/cli@0.1.23
COPY --chown=garimpei:garimpei . /app
RUN uv sync --frozen --all-groups && mkdir -p /tmp/g23tmp && chown garimpei:garimpei /tmp/g23tmp && chown -R garimpei:garimpei /app
USER garimpei
ENTRYPOINT []
CMD ["node", "/app/scripts/run-gates.mjs"]
