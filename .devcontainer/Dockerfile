FROM mcr.microsoft.com/devcontainers/python:3.12

# ── System dependencies for Chromium (Puppeteer) and Pandoc ──────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Chromium runtime libraries
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
    libxcomposite1 libxdamage1 libxrandr2 libgbm1 libpango-1.0-0 \
    libcairo2 libasound2 libxshmfence1 libx11-xcb1 libxkbcommon0 \
    fonts-liberation libappindicator3-1 \
    # Pandoc
    pandoc \
    # Utilities
    jq \
    && rm -rf /var/lib/apt/lists/*

# ── Node.js 20 LTS ──────────────────────────────────────────────────────────
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# ── Mermaid CLI (mmdc) — installs Puppeteer + bundled Chromium ───────────────
ENV PUPPETEER_CACHE_DIR=/opt/puppeteer-cache
RUN npm install -g @mermaid-js/mermaid-cli \
    && npm cache clean --force

# Puppeteer launch flags for containerized Chromium (no sandbox needed —
# the container itself is the sandbox boundary)
RUN echo '{"args":["--no-sandbox","--disable-setuid-sandbox","--disable-dev-shm-usage"]}' \
    > /opt/puppeteer-config.json
ENV PUPPETEER_CONFIG=/opt/puppeteer-config.json

# ── Vale prose linter ─────────────────────────────────────────────────────
ARG VALE_VERSION=3.9.5
RUN curl -fsSL "https://github.com/errata-ai/vale/releases/download/v${VALE_VERSION}/vale_${VALE_VERSION}_Linux_64-bit.tar.gz" \
    | tar xz -C /usr/local/bin vale

# Pre-download Vale style packages for offline use (network_mode: none at runtime)
COPY .vale-bootstrap.ini /tmp/.vale.ini
RUN cd /tmp && vale sync \
    && mv .vale/styles /opt/vale-styles \
    && rm .vale.ini

# ── Python dependencies (pre-installed so editable install works offline) ────
RUN pip install --no-cache-dir \
    "python-docx>=1.1.0" \
    "PyYAML>=6.0" \
    "mistune>=3.0" \
    "lxml>=4.9"
