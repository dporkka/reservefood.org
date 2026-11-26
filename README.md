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
- **Styling:** Plain CSS (no framework dependencies)
- **Hosting:** Deployable to any static host (Netlify, Cloudflare Pages, GitHub Pages, etc.)

---

## Local Development

### Prerequisites

- [Hugo](https://gohugo.io/installation/) (extended version recommended)

### Running locally

```bash
hugo server
```

The site will be available at `http://localhost:1313`.

### Building for production

```bash
hugo
```

Output is written to the `public/` directory.

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
│       └── main.css      # Site stylesheet
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

## Portability checks

The site can be served at a domain root or a nested deployment prefix. Build
and test with the canonical base URL set to the deployment location:

```sh
hugo --minify --baseURL https://example.org/reserve/
python3 -m unittest discover -s tests -v
```

The tests build both root and subpath variants, resolve local links and assets,
and check the sitemap URL and active navigation. The mobile navigation browser
test is optional and uses developer-installed Playwright and Chromium; the
rest of the checks require only Hugo and the Python standard library.
Use `HUGO_BIN` to specify Hugo and set `CHROMIUM_BIN` to an installed
Chromium executable to enable the browser check.
The menu remains visible without JavaScript; JavaScript enhances it with a
collapsible mobile toggle.
