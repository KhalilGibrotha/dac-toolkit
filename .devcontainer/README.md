# Devcontainer — DAC Toolkit

Fully offline containerized development environment for the documentation-as-code pipeline.

All dependencies (Python, Node.js, mmdc/Chromium, Pandoc) are baked into the image at build time.

---

## Container Engine Setup

### Option A: Podman (home / org workstation)

1. Install [Podman Desktop](https://podman-desktop.io/) (Windows) or `podman` (Linux)
2. Install `podman-compose`:

   ```bash
   pip install podman-compose
   ```

3. Configure VS Code to use Podman — add to your **User** settings (not workspace):

   ```jsonc
   {
     "dev.containers.dockerPath": "podman",
     "dev.containers.dockerComposePath": "podman-compose"
   }
   ```

4. Open this repo in VS Code and select **Reopen in Container**
5. Runtime enforces `network_mode: none` — zero outbound connections

### Option B: Docker Desktop

1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/)
2. Open this repo in VS Code and select **Reopen in Container**
3. Runtime enforces `network_mode: none` — zero outbound connections

### Option C: OpenShift Dev Spaces

Dev Spaces uses `devfile.yaml` (at the repo root), not `devcontainer.json`.

**Quick start (UDI image):**

1. In your Dev Spaces dashboard, create a new workspace from the toolkit repo URL
2. Dev Spaces detects `devfile.yaml` automatically
3. The `postStart` event installs mmdc and docx_builder on first launch
4. Network isolation is handled by OpenShift NetworkPolicy — not `network_mode`

**Air-gapped / pre-built image (recommended for production):**

1. Stage the pinned starter vendor tree. CI does this before every build, so a
   bare `podman build` fails at `COPY starter-vendor`. Use the `STARTER_REF`
   pinned in `.github/workflows/docker-build.yml`:

   ```bash
   git clone --depth 1 --branch v1.1.1 \
     https://github.com/KhalilGibrotha/dac-starter starter-vendor-src
   python3 scripts/gen-stock-hashes.py --starter starter-vendor-src --verify
   mkdir -p starter-vendor/files
   cp -r starter-vendor-src/. starter-vendor/files/
   rm -rf starter-vendor/files/.git
   cp starter-vendor-src/stock-hashes.json starter-vendor/
   python3 scripts/gen-stock-hashes.py --starter starter-vendor-src \
     --emit-manifest starter-vendor/manifest.json \
     --starter-version v1.1.1 --engine-image dac-toolkit:local
   ```

2. Build — on Windows, from a `git archive` staging directory, never the
   worktree. A worktree COPY bakes checkout artifacts into the image: a CRLF
   shebang on `dac-init` shipped exactly this way and broke it inside the
   image, while CI, building from a Linux checkout, stayed green.

   ```bash
   mkdir -p /tmp/ctx && git archive HEAD | tar -x -C /tmp/ctx
   cp -r starter-vendor /tmp/ctx/
   podman build -f .devcontainer/Dockerfile.devspaces \
     -t <your-registry>/dac-toolkit:latest /tmp/ctx
   ```

3. Validate before pushing: run the Release QA steps
   (`.github/workflows/qa.yml`) against the built tag — toolchain presence
   including quarto and render-decks.sh, a deck render, the starter-tree
   verify, dac-init idempotence, and a docx render.

4. Push, then edit `devfile.yaml` — replace the `image:` line in the `tools`
   component
5. Remove or comment out the `install-tools` postStart event (tools are already in the image)
6. Add your content repos to the `projects:` block in `devfile.yaml`

---

## What's Installed

| Tool | Version | Purpose |
|---|---|---|
| Python | 3.12 | docx_builder runtime |
| Node.js | 20 LTS | mmdc runtime |
| mmdc | latest | Mermaid diagram to PNG rendering |
| Chromium | bundled via Puppeteer | Headless browser for mmdc |
| Pandoc | apt/dnf default | Additional document conversion |
| docx-build | editable install | Markdown to styled DOCX |

---

## Terminal Editors (Dev Spaces image)

The Dev Spaces image (`Dockerfile.devspaces`) ships vim (full, not
vim-minimal) and nano with system-wide prose defaults tuned for this
workspace: the characters the content-repo CI rejects — smart quotes,
non-breaking spaces, mojibake — are highlighted in red, tabs and trailing
whitespace are visible, spell check is on for Markdown, and soft wrap breaks
at word boundaries without inserting hard line breaks. YAML gets two-space
indentation and highlighting (RHEL 9's nano predates upstream's yaml.nanorc,
so the image carries one).

These are defaults, not mandates:

- vim: settings live in `/etc/vimrc.local`, sourced before `~/.vimrc`, so a
  personal vimrc overrides anything (or `autocmd! dacprose` to drop the
  filetype behavior wholesale).
- nano: settings are appended to `/etc/nanorc`, read before `~/.nanorc` /
  `~/.config/nano/nanorc`, so personal config wins. Toggle whitespace display
  with `M-P`.
- neovim is not in the image (not available from free UBI9 repos). A
  user-supplied nvim can adopt the same defaults with
  `source /etc/vimrc.local` in its init file.

---

## Verify the Environment

```bash
# Network isolation — Podman/Docker only (both should fail)
ping -c1 8.8.8.8
curl https://google.com

# Tools
mmdc --version
pandoc --version
docx-build --help

# Render a test diagram
echo 'graph TD; A-->B' | mmdc -i - -o /tmp/test.png -p "${PUPPETEER_CONFIG}"

# Build a test document
docx-build docx_builder/examples/sample_input.md -o /tmp/test.docx
```

---

## Multi-Repo Workspace

The toolkit is designed to work alongside one or more content repos. In Dev Spaces,
add content repos to the `projects:` block in `devfile.yaml`. For local Podman/Docker,
clone content repos alongside the toolkit and run build scripts with the content directory:

```bash
bash scripts/build-docs.sh /path/to/content-repo
```

---

## Files Overview

| File | Used by |
|---|---|
| `.devcontainer/devcontainer.json` | VS Code + Podman/Docker |
| `.devcontainer/docker-compose.yml` | VS Code + Podman/Docker |
| `.devcontainer/Dockerfile` | VS Code + Podman/Docker |
| `.devcontainer/Dockerfile.devspaces` | Dev Spaces (pre-built image) |
| `devfile.yaml` | Dev Spaces |
