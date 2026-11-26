"""Optional developer checks; production still requires only Hugo."""
import functools
import hashlib
from html.parser import HTMLParser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import os
import re
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import unittest
from urllib.parse import unquote, urljoin, urlsplit

ROOT = Path(__file__).resolve().parents[1]
HUGO = os.environ.get("HUGO_BIN") or shutil.which("hugo")


class References(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.current = []
        self.ids = set()
        self.stylesheets = []
        self.body_classes = set()
        self.headings = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if "id" in values:
            self.ids.add(values["id"])
        if tag == "link" and values.get("rel") == "stylesheet":
            self.stylesheets.append(values["href"])
        if tag == "body":
            self.body_classes = set(values.get("class", "").split())
        if tag in {"h1", "h2", "h3", "h4"}:
            self.headings.append(tag)
        if tag in {"a", "link", "script", "img"}:
            url = values.get("href") or values.get("src")
            if url:
                self.links.append(url)
        if tag == "a" and values.get("aria-current") == "page":
            self.current.append(values["href"])


def contrast_ratio(first, second):
    def luminance(color):
        channels = [int(value) / 255 for value in re.findall(r"\d+", color)]
        if len(channels) != 3:
            raise ValueError(f"Expected opaque computed RGB: {color}")
        linear = [value / 12.92 if value <= 0.04045
                  else ((value + 0.055) / 1.055) ** 2.4 for value in channels]
        return sum(value * weight for value, weight in zip(linear, (0.2126, 0.7152, 0.0722)))

    dark, light = sorted((luminance(first), luminance(second)))
    return (light + 0.05) / (dark + 0.05)


def build(destination, base_url):
    subprocess.run([HUGO, "--source", str(ROOT), "--destination", str(destination),
                    "--baseURL", base_url, "--minify", "--panicOnWarning"], check=True)


@unittest.skipUnless(HUGO, "Set HUGO_BIN or install Hugo")
class StaticSiteTests(unittest.TestCase):
    def test_vendored_syntyr_integrity(self):
        vendor = ROOT / "static/css/vendor/syntyr"
        manifest = dict(line.split()[::-1]
                        for line in (vendor / "SHA256SUMS").read_text().splitlines())
        self.assertEqual(set(manifest), {"syntyr.core.css", "syntyr.semantic.css", "LICENSE"})
        for name, expected in manifest.items():
            self.assertEqual(hashlib.sha256((vendor / name).read_bytes()).hexdigest(),
                             expected, name)
        self.assertIn("MIT License", (vendor / "LICENSE").read_text())


    def test_root_and_prefix_assets_navigation_and_robots(self):
        for prefix in ("/", "/reserve/"):
            with self.subTest(prefix=prefix), tempfile.TemporaryDirectory() as temp:
                output = Path(temp)
                base = "https://example.org" + prefix
                build(output, base)
                pages = sorted(output.rglob("*.html"))
                self.assertGreaterEqual(len(pages), 11)
                for page in pages:
                    parser = References()
                    parser.feed(page.read_text())
                    path = page.relative_to(output).as_posix()
                    self.assertIn("syn-root", parser.body_classes, path)
                    self.assertEqual(parser.stylesheets, [
                        prefix + "css/vendor/syntyr/syntyr.core.css",
                        prefix + "css/vendor/syntyr/syntyr.semantic.css",
                        prefix + "css/main.css",
                    ], path)
                    self.assertEqual(parser.headings.count("h1"), 1, path)
                    self.assertEqual(parser.headings[0], "h1", path)
                    for link in parser.links:
                        uri = urlsplit(urljoin(base + path, link))
                        if uri.netloc != "example.org":
                            continue
                        self.assertTrue(uri.path.startswith(prefix), (path, link))
                        target = output / unquote(uri.path[len(prefix):])
                        if target.is_dir():
                            target /= "index.html"
                        self.assertTrue(target.is_file(), (path, link))
                        if uri.fragment and target.suffix == ".html":
                            linked = References()
                            linked.feed(target.read_text())
                            self.assertIn(unquote(uri.fragment), linked.ids, (path, link))
                    if path == "contact/index.html":
                        self.assertEqual(parser.current, [prefix + "contact/"])
                self.assertIn(base + "sitemap.xml", (output / "robots.txt").read_text())

    def test_mobile_nav_with_and_without_javascript(self):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            self.skipTest("Optional Playwright is not installed")
        chromium = os.environ.get("CHROMIUM_BIN")
        if not chromium:
            self.skipTest("Set CHROMIUM_BIN to enable the optional real browser check")
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            handler = functools.partial(SimpleHTTPRequestHandler, directory=directory)
            with ThreadingHTTPServer(("127.0.0.1", 0), handler) as server:
                base = f"http://127.0.0.1:{server.server_port}/reserve/"
                build(directory / "reserve", base)
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                try:
                    with sync_playwright() as p:
                        browser = p.chromium.launch(executable_path=chromium, headless=True)
                        for enabled in (False, True):
                            with self.subTest(javascript=enabled):
                                context = browser.new_context(java_script_enabled=enabled,
                                                              viewport={"width": 390, "height": 844})
                                try:
                                    # Analytics is unrelated to the local menu contract.
                                    context.route("**/*", lambda route: route.continue_()
                                                  if route.request.url.startswith(base) else route.abort())
                                    page = context.new_page()
                                    page.goto(base, wait_until="load")
                                    toggle = page.locator(".nav-toggle")
                                    menu = page.locator("#nav-menu")
                                    if enabled:
                                        self.assertTrue(toggle.is_visible())
                                        self.assertFalse(menu.is_visible())
                                        toggle.click()
                                        self.assertEqual(toggle.get_attribute("aria-expanded"), "true")
                                        self.assertTrue(menu.is_visible())
                                        toggle.click()
                                        self.assertFalse(menu.is_visible())
                                        toggle.click()
                                    else:
                                        self.assertFalse(toggle.is_visible())
                                        self.assertTrue(menu.is_visible())
                                    menu.get_by_role("link", name="Contact").click()
                                    self.assertEqual(page.url, base + "contact/")
                                finally:
                                    context.close()
                        for theme in ("light", "dark"):
                            for width in (320, 390, 768, 1280):
                                with self.subTest(theme=theme, width=width):
                                    context = browser.new_context(
                                        java_script_enabled=False, color_scheme=theme, reduced_motion="reduce",
                                        viewport={"width": width, "height": 900})
                                    try:
                                        context.route("**/*", lambda route: route.continue_()
                                                      if route.request.url.startswith(base) else route.abort())
                                        page = context.new_page()
                                        for path in ("", "about/", "product/", "programs/",
                                                     "governments-ngos/", "investors/", "faq/",
                                                     "contact/", "privacy/", "terms/", "404.html"):
                                            page.goto(base + path, wait_until="load")
                                            self.assertTrue(page.locator("#nav-menu").is_visible())
                                            self.assertEqual(page.locator("body").evaluate(
                                                "(el) => getComputedStyle(el).colorScheme"), theme)
                                            self.assertLessEqual(page.evaluate(
                                                "document.documentElement.scrollWidth"), width, path)
                                            self.assertEqual(page.locator("h1").count(), 1, path)
                                        page.goto(base, wait_until="load")
                                        page.keyboard.press("Tab")
                                        self.assertTrue(page.locator(".skip-link").evaluate(
                                            "(el) => el === document.activeElement"))
                                        page.keyboard.press("Enter")
                                        self.assertTrue(page.locator("main").evaluate(
                                            "(el) => el === document.activeElement"))
                                        primary = page.get_by_role("link", name="Explore Product")
                                        secondary = page.get_by_role("link", name="Contact Sales")
                                        expected = ("rgb(15, 118, 110)" if theme == "light"
                                                    else "rgb(94, 234, 212)")
                                        self.assertEqual(primary.evaluate(
                                            "(el) => getComputedStyle(el).backgroundColor"), expected)
                                        self.assertGreaterEqual(primary.bounding_box()["height"], 44)
                                        self.assertGreaterEqual(secondary.bounding_box()["height"], 44)
                                        for state in ("default", "hover"):
                                            if state == "hover":
                                                primary.hover()
                                                self.assertEqual(primary.evaluate(
                                                    "(el) => getComputedStyle(el).backgroundColor"),
                                                    "rgb(13, 105, 98)" if theme == "light"
                                                    else "rgb(133, 243, 225)")
                                            foreground, background = primary.evaluate(
                                                "(el) => { const style = getComputedStyle(el); return [style.color, style.backgroundColor]; }")
                                            self.assertGreaterEqual(contrast_ratio(foreground, background), 4.5)
                                        primary.click()
                                        self.assertEqual(page.url, base + "product/")
                                    finally:
                                        context.close()
                        browser.close()
                finally:
                    server.shutdown()
                    thread.join()


if __name__ == "__main__":
    unittest.main()
