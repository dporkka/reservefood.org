"""Optional developer checks; production still requires only Hugo."""
import functools
from html.parser import HTMLParser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import os
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

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag in {"a", "link", "script", "img"}:
            url = values.get("href") or values.get("src")
            if url:
                self.links.append(url)
        if tag == "a" and values.get("aria-current") == "page":
            self.current.append(values["href"])


def build(destination, base_url):
    subprocess.run([HUGO, "--source", str(ROOT), "--destination", str(destination),
                    "--baseURL", base_url, "--minify"], check=True)


@unittest.skipUnless(HUGO, "Set HUGO_BIN or install Hugo")
class StaticSiteTests(unittest.TestCase):
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
                    for link in parser.links:
                        uri = urlsplit(urljoin(base + path, link))
                        if uri.netloc != "example.org":
                            continue
                        self.assertTrue(uri.path.startswith(prefix), (path, link))
                        target = output / unquote(uri.path[len(prefix):])
                        if target.is_dir():
                            target /= "index.html"
                        self.assertTrue(target.is_file(), (path, link))
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
                        browser.close()
                finally:
                    server.shutdown()
                    thread.join()


if __name__ == "__main__":
    unittest.main()
