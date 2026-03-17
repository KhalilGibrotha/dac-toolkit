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

1. Build the Dev Spaces-specific image and push to your internal registry:

   ```bash
   podman build -f .devcontainer/Dockerfile.devspaces \
     -t <your-registry>/dac-toolkit:latest .
   podman push <your-registry>/dac-toolkit:latest
   ```

2. Edit `devfile.yaml` — replace the `image:` line in the `tools` component
3. Remove or comment out the `install-tools` postStart event (tools are already in the image)
4. Add your content repos to the `projects:` block in `devfile.yaml`

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
