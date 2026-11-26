# Reserve Food

**Long-life nutrition infrastructure.**

Reserve Food builds shelf-stable nutrition designed for daily use and long-term storage—without refrigeration and without fragile supply chains.

---

## Overview

This repository contains the source code for [reservefood.org](https://reservefood.org), a static website built with [Hugo](https://gohugo.io/).

The site provides information about Reserve Food's products, programs, investor relations, and contact details.

---

## Tech Stack

- **Static site generator:** [Hugo](https://gohugo.io/)
- **Templating:** Go HTML templates
- **Styling:** [Syntyr CSS](https://github.com/dporkka/syntyr-css) v0.3.0-alpha.4 (vendored core + semantic CSS) and a small Reserve Food brand stylesheet
- **Hosting:** Deployable to any static host (Netlify, Cloudflare Pages, GitHub Pages, etc.)

---

## Local Development

### Prerequisites

- [Hugo 0.170.0](https://gohugo.io/installation/) (standard build; no Extended/Sass requirement)

### Running locally

```bash
hugo server
```

The site will be available at `http://localhost:1313`.

### Building for production

```bash
hugo
```

Output is written to the `public/` directory. The existing GitHub Pages
workflow builds only this generated directory with the same pinned Hugo
version. Do not upload the source repository as a static-site artifact.

---

## Project Structure

```
reservefood.org/
├── content/              # Markdown content pages
│   ├── _index.md         # Homepage content
│   ├── about.md
│   ├── contact.md
│   ├── faq.md
│   ├── governments-ngos.md
│   ├── investors.md
│   ├── product.md
│   └── programs.md
├── layouts/              # Hugo HTML templates
│   ├── _default/
│   │   ├── baseof.html   # Base layout template
│   │   └── single.html   # Single page template
│   ├── index.html        # Homepage template
│   └── partials/
│       ├── header.html
│       └── footer.html
├── static/
│   └── css/
│       ├── main.css      # Brand tokens and site-specific composition
│       └── vendor/syntyr/ # Pinned MIT-licensed Syntyr CSS
├── hugo.toml             # Hugo configuration
├── PRD.md                # Product Requirements Document
└── README.md             # This file
```

---

## Pages

| Path | Description |
|------|-------------|
| `/` | Homepage — product summary and mission |
| `/about/` | Company background and design philosophy |
| `/product/` | Reserve Food Bar specifications |
| `/programs/` | Household, institutional, and community programs |
| `/governments-ngos/` | Government and NGO procurement information |
| `/investors/` | Investor overview and business model |
| `/faq/` | Frequently asked questions |
| `/contact/` | Contact information and partnership inquiries |

---

## Contributing

See [PRD.md](PRD.md) for the product roadmap and remaining tasks.

---

## License

&copy; Reserve Food. All rights reserved.

## Syntyr styling

The site uses the published Syntyr release, not the unreleased source candidate.
Core provides the scoped reset, layout, focus, typography and controls;
semantic mode styles native HTML rendered from Markdown. The local
`main.css` overrides the public `--syn-*` tokens for the Reserve Food palette
and keeps the reading-width layout and progressively enhanced navigation.
There is no Tailwind, npm, Hugo module, CSS preprocessor or remote CSS dependency.

The unmodified copies, MIT license, source commit and SHA-256 checksums are in
[`static/css/vendor/syntyr/`](static/css/vendor/syntyr/README.md).
Hugo builds offline with these committed files. Upgrade only by choosing a
published release and following the vendoring instructions, then rerun the tests.
The vendor files are not Reserve Food proprietary content.

## Portability checks

The site can be served at a domain root or a nested deployment prefix. Build
and test with the canonical base URL set to the deployment location:

```sh
hugo --minify --baseURL https://example.org/reserve/
python3 -m unittest discover -s tests -v
```

The tests build both root and subpath variants, resolve local links, fragments
and assets, and check the sitemap, active navigation and the vendor hashes.
The test suite also compares complete output trees using two simulated build
clocks ten years apart. The footer is intentionally timeless, avoiding an
annual copyright-year edit or rebuild. The existing Pages build checks the
vendored SHA-256 manifest before running Hugo; deployment privileges are
limited to the deployment job.
The optional Playwright/Chromium check exercises every page at 320, 390, 768
and 1280 CSS pixels in both light and dark modes, checks keyboard skip
navigation, mobile toggling with and without JavaScript, reflow, and primary
button contrast. The non-browser checks require only Hugo and the Python
standard library.
For the optional browser check, install Python Playwright in a virtual
environment and use an existing compatible Chromium executable (or install
Chromium using `python -m playwright install chromium`). For example:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install playwright
HUGO_BIN=/path/to/hugo CHROMIUM_BIN=/path/to/chromium \
  python -m unittest discover -s tests -v
```

Replace the executable paths with the actual local paths. Confirm the browser
check reports `ok`, not `skipped`. These are optional test-only tools, not
site build or runtime dependencies.
The menu remains visible without JavaScript; JavaScript enhances it with a
collapsible mobile toggle.

## Long-term preservation

Keep a source archive, the exact pinned Hugo binary for your platform,
and a static build together. On GNU/Linux, for an unchanged source
checkout and a fixed production base URL:

```sh
(cd static/css/vendor/syntyr && sha256sum -c SHA256SUMS)
hugo --minify --panicOnWarning --destination /tmp/reservefood-static
tar --sort=name --mtime=@0 --owner=0 --group=0 --numeric-owner \
  -cf /tmp/reservefood-static.tar -C /tmp/reservefood-static .
sha256sum /tmp/reservefood-static.tar > /tmp/reservefood-static.tar.sha256
```

Build into a new output directory; only publish the generated static files.
The archive can be served by an ordinary static HTTP server. Its links use
the configured production base path; it is not a file:// site. Do not
include credentials or other source-only files in the public archive.
