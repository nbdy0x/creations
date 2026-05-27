#!/usr/bin/env python3
"""
Web Cloner / Website Downloader + Path Bruteforce
Mirip saveweb2zip.com — bisa crawl normal + coba path umum yang tidak ter-link
"""

import os
import re
import sys
import time
import zipfile
import hashlib
import argparse
import threading
import urllib.parse
from pathlib import Path
from queue import Queue
from collections import deque
from urllib.robotparser import RobotFileParser
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import requests
    from bs4 import BeautifulSoup
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
except ImportError:
    print("[!] Dependency kurang. Jalankan dulu:")
    print("    pip install requests beautifulsoup4")
    sys.exit(1)


# ─── KONFIGURASI DEFAULT ──────────────────────────────────────────────────────

DEFAULT_CONFIG = {
    "max_depth":        3,
    "max_pages":        500,
    "delay":            0.3,
    "timeout":          12,
    "user_agent":       "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "output_dir":       "output",
    "create_zip":       True,
    "respect_robots":   False,      # Default OFF — kita owner sendiri
    "same_domain_only": True,
    "max_url_length":   500,
    "bruteforce":       False,      # Aktifkan dengan --bruteforce
    "bf_threads":       10,         # Thread paralel untuk bruteforce
    "bf_delay":         0.1,        # Jeda per request bruteforce
}

# ─── DAFTAR PATH BRUTEFORCE ───────────────────────────────────────────────────
# File & folder yang SANGAT umum ada di public_html tapi mungkin tidak ter-link

BRUTEFORCE_PATHS = [
    # ── Root files ──────────────────────────────────────────────────────────
    "/",
    "/index.html", "/index.php", "/index.htm",
    "/home.html", "/home.php",
    "/default.html", "/default.php",
    "/robots.txt", "/sitemap.xml", "/sitemap_index.xml",
    "/.htaccess",
    "/favicon.ico", "/favicon.png",
    "/humans.txt", "/security.txt",
    "/manifest.json", "/browserconfig.xml",
    "/crossdomain.xml",

    # ── Halaman umum ────────────────────────────────────────────────────────
    "/about", "/about.php", "/about.html", "/about-us", "/about-us.php",
    "/contact", "/contact.php", "/contact.html", "/contact-us",
    "/services", "/services.php",
    "/products", "/products.php",
    "/portfolio", "/portfolio.php",
    "/blog", "/blog.php", "/news", "/news.php",
    "/faq", "/faq.php",
    "/login", "/login.php", "/signin", "/signin.php",
    "/register", "/register.php", "/signup", "/signup.php",
    "/dashboard", "/dashboard.php",
    "/profile", "/profile.php",
    "/admin", "/admin.php", "/admin/index.php", "/admin/login.php",
    "/administrator", "/administrator/index.php",
    "/panel", "/panel.php", "/cp", "/cp.php",
    "/logout", "/logout.php",
    "/search", "/search.php",
    "/404.html", "/404.php", "/error.html", "/error.php",
    "/maintenance.html", "/maintenance.php",
    "/coming-soon.html", "/coming-soon.php",
    "/terms", "/terms.php", "/terms-of-service",
    "/privacy", "/privacy.php", "/privacy-policy",
    "/sitemap", "/sitemap.php",
    "/feed", "/feed.xml", "/rss.xml", "/atom.xml",

    # ── PHP umum ────────────────────────────────────────────────────────────
    "/config.php", "/configuration.php", "/settings.php",
    "/functions.php", "/helper.php", "/helpers.php",
    "/init.php", "/bootstrap.php", "/autoload.php",
    "/header.php", "/footer.php", "/sidebar.php",
    "/ajax.php", "/api.php", "/callback.php", "/webhook.php",
    "/auth.php", "/verify.php", "/activate.php",
    "/upload.php", "/download.php",
    "/process.php", "/submit.php", "/send.php",
    "/payment.php", "/checkout.php", "/cart.php",
    "/cron.php", "/task.php",
    "/test.php", "/info.php", "/phpinfo.php",

    # ── Folder umum ─────────────────────────────────────────────────────────
    "/assets/", "/asset/",
    "/static/",
    "/public/",
    "/css/", "/styles/", "/style/",
    "/js/", "/javascript/", "/scripts/", "/script/",
    "/img/", "/images/", "/image/", "/imgs/",
    "/fonts/", "/font/",
    "/icons/", "/icon/",
    "/media/", "/medias/",
    "/uploads/", "/upload/", "/files/", "/file/",
    "/documents/", "/docs/",
    "/downloads/", "/download/",
    "/videos/", "/video/",
    "/audio/", "/music/",
    "/data/",
    "/api/", "/api/v1/", "/api/v2/",
    "/includes/", "/include/",
    "/lib/", "/libs/", "/library/", "/libraries/",
    "/vendor/",
    "/plugins/", "/plugin/",
    "/modules/", "/module/",
    "/components/", "/component/",
    "/templates/", "/template/", "/themes/", "/theme/",
    "/views/", "/view/",
    "/pages/", "/page/",
    "/layouts/", "/layout/",
    "/partials/",
    "/helpers/", "/helper/",
    "/config/", "/configs/",
    "/lang/", "/languages/", "/locale/",
    "/backup/", "/backups/", "/bak/",
    "/logs/", "/log/",
    "/cache/", "/tmp/", "/temp/",
    "/src/", "/source/",
    "/build/", "/dist/",
    "/database/", "/db/",
    "/sql/",
    "/cgi-bin/",
    "/wp-content/", "/wp-includes/", "/wp-admin/",   # WordPress
    "/wp-login.php", "/wp-config.php", "/wp-cron.php",
    "/xmlrpc.php",                                    # WordPress XML-RPC
    "/wp-content/uploads/",
    "/wp-content/themes/",
    "/wp-content/plugins/",
    "/joomla/", "/administrator/",                   # Joomla
    "/administrator/index.php",
    "/components/", "/modules/",
    "/drupal/", "/sites/default/",                   # Drupal
    "/magento/",                                     # Magento

    # ── File konfigurasi yg kadang ter-expose ────────────────────────────────
    "/.env",
    "/web.config",
    "/composer.json", "/composer.lock",
    "/package.json", "/package-lock.json",
    "/.gitignore",
    "/README.md", "/readme.md", "/CHANGELOG.md",

    # ── Asset root umum ─────────────────────────────────────────────────────
    "/logo.png", "/logo.jpg", "/logo.svg", "/logo.webp",
    "/banner.jpg", "/banner.png",
    "/bg.jpg", "/bg.png", "/background.jpg",
    "/hero.jpg", "/hero.png",
    "/style.css", "/styles.css", "/main.css", "/app.css",
    "/main.js", "/app.js", "/bundle.js",
    "/jquery.js", "/jquery.min.js",
]

# Ekstensi aset statis
ASSET_EXTENSIONS = {
    ".css", ".js", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".ico",
    ".webp", ".woff", ".woff2", ".ttf", ".eot", ".otf", ".mp4", ".webm",
    ".pdf", ".json", ".xml", ".map", ".txt", ".zip", ".rar",
}

URL_TAG_ATTRS = {
    "a":      ["href"],
    "link":   ["href"],
    "script": ["src"],
    "img":    ["src", "data-src", "srcset"],
    "source": ["src", "srcset"],
    "video":  ["src", "poster"],
    "audio":  ["src"],
    "iframe": ["src"],
    "form":   ["action"],
}

META_URL_PROPERTIES = {
    "og:image", "og:image:url", "og:image:secure_url",
    "og:video", "og:video:url", "og:video:secure_url",
    "og:audio", "og:audio:url", "og:audio:secure_url",
    "og:url",
    "twitter:image", "twitter:image:src", "twitter:player",
    "thumbnail", "msapplication-tileimage",
}


# ─── VALIDASI URL ─────────────────────────────────────────────────────────────

def is_valid_url_string(raw: str, max_len: int = 500) -> bool:
    if not raw or len(raw) > max_len:
        return False
    if " " in raw:
        return False
    for bad in ("\n", "\r", "\t"):
        if bad in raw:
            return False
    return True


def normalize_url(raw: str, base: str, max_len: int = 500) -> str | None:
    if not is_valid_url_string(raw, max_len):
        return None
    try:
        abs_url = urllib.parse.urljoin(base, raw)
        parsed = urllib.parse.urlparse(abs_url)
        if parsed.scheme not in ("http", "https"):
            return None
        if not parsed.netloc:
            return None
        clean = parsed._replace(fragment="").geturl()
        if len(clean) > max_len:
            return None
        return clean
    except Exception:
        return None


# ─── PATH HELPER ──────────────────────────────────────────────────────────────

def url_to_filepath(url: str, output_dir: str) -> str:
    parsed = urllib.parse.urlparse(url)
    domain_part = parsed.netloc
    path_part = parsed.path.lstrip("/")

    if not path_part or path_part.endswith("/"):
        path_part = os.path.join(path_part, "index.html")

    if parsed.query:
        stem, ext = os.path.splitext(path_part)
        q_hash = hashlib.md5(parsed.query.encode()).hexdigest()[:8]
        path_part = f"{stem}_{q_hash}{ext}"

    if not os.path.splitext(path_part)[1]:
        path_part += ".html"

    return os.path.join(output_dir, domain_part, path_part)


def _rel(target_fp: str, page_fp: str) -> str:
    return os.path.relpath(
        target_fp, os.path.dirname(page_fp)
    ).replace("\\", "/")


# ─── SESSION ──────────────────────────────────────────────────────────────────

def make_session(config: dict) -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=2,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=20, pool_maxsize=20)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({"User-Agent": config["user_agent"]})
    return session


# ─── SRCSET ───────────────────────────────────────────────────────────────────

def extract_srcset_urls(srcset: str) -> list[str]:
    urls = []
    for part in srcset.split(","):
        part = part.strip()
        if part:
            tokens = part.split()
            if tokens:
                urls.append(tokens[0])
    return urls


# ─── HTML / CSS REWRITER ─────────────────────────────────────────────────────

def rewrite_html(content: str, page_url: str, output_dir: str, max_url_len: int) -> str:
    soup = BeautifulSoup(content, "html.parser")
    page_fp = url_to_filepath(page_url, output_dir)

    for tag, attrs in URL_TAG_ATTRS.items():
        for el in soup.find_all(tag):
            for attr in attrs:
                val = el.get(attr, "")
                if not val:
                    continue
                if attr == "srcset":
                    new_parts = []
                    for part in val.split(","):
                        part = part.strip()
                        if not part:
                            continue
                        tokens = part.split()
                        raw = tokens[0]
                        abs_url = normalize_url(raw, page_url, max_url_len)
                        if abs_url:
                            tokens[0] = _rel(url_to_filepath(abs_url, output_dir), page_fp)
                        new_parts.append(" ".join(tokens))
                    el[attr] = ", ".join(new_parts)
                else:
                    abs_url = normalize_url(val, page_url, max_url_len)
                    if abs_url:
                        el[attr] = _rel(url_to_filepath(abs_url, output_dir), page_fp)

    for el in soup.find_all("meta"):
        prop = (el.get("property") or el.get("name") or "").lower().strip()
        if prop not in META_URL_PROPERTIES:
            continue
        val = el.get("content", "")
        abs_url = normalize_url(val, page_url, max_url_len)
        if abs_url:
            el["content"] = _rel(url_to_filepath(abs_url, output_dir), page_fp)

    for el in soup.find_all(style=True):
        el["style"] = rewrite_css_urls(el["style"], page_url, output_dir, max_url_len, page_fp)

    for style_el in soup.find_all("style"):
        if style_el.string:
            style_el.string = rewrite_css_urls(
                style_el.string, page_url, output_dir, max_url_len, page_fp)

    return str(soup)


def rewrite_css_urls(css: str, base_url: str, output_dir: str,
                     max_url_len: int, ref_fp: str = None) -> str:
    if ref_fp is None:
        ref_fp = url_to_filepath(base_url, output_dir)

    def replacer(match):
        raw = match.group(1).strip("'\" ")
        abs_url = normalize_url(raw, base_url, max_url_len)
        if not abs_url:
            return match.group(0)
        return f"url('{_rel(url_to_filepath(abs_url, output_dir), ref_fp)}')"

    return re.sub(r'url\(\s*([^)]+?)\s*\)', replacer, css)


# ─── ZIP ──────────────────────────────────────────────────────────────────────

def zip_output(output_dir: str, zip_path: str):
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(output_dir):
            for f in files:
                full = os.path.join(root, f)
                arcname = os.path.relpath(full, os.path.dirname(output_dir))
                zf.write(full, arcname)


# ─── CRAWLER ──────────────────────────────────────────────────────────────────

class WebCloner:
    def __init__(self, start_url: str, config: dict):
        self.start_url    = start_url.rstrip("/")
        self.config       = config
        self.parsed_base  = urllib.parse.urlparse(start_url)
        self.base_domain  = self.parsed_base.netloc
        self.base_origin  = f"{self.parsed_base.scheme}://{self.base_domain}"
        self.output_dir   = config["output_dir"]
        self.session      = make_session(config)
        self.visited: set[str]   = set()
        self._visited_lock        = threading.Lock()
        self.queue: deque        = deque()
        self.downloaded: list[str] = []
        self._dl_lock             = threading.Lock()
        self.failed: list[str]   = []
        self._fail_lock           = threading.Lock()
        self.robots               = None
        self.max_url              = config.get("max_url_length", 500)
        self._print_lock          = threading.Lock()
        self._page_count          = 0
        self._page_lock           = threading.Lock()

        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

    # ── Logging thread-safe ───────────────────────────────────────────────────

    def log(self, msg: str):
        with self._print_lock:
            print(msg)

    # ── robots.txt ────────────────────────────────────────────────────────────

    def load_robots(self):
        robots_url = f"{self.base_origin}/robots.txt"
        rp = RobotFileParser()
        rp.set_url(robots_url)
        try:
            rp.read()
            self.robots = rp
            self.log("  [robots] robots.txt dibaca")
        except Exception:
            self.log("  [robots] Tidak ada robots.txt")

    def is_allowed(self, url: str) -> bool:
        if not self.config["respect_robots"] or self.robots is None:
            return True
        return self.robots.can_fetch(self.config["user_agent"], url)

    # ── Fetch ─────────────────────────────────────────────────────────────────

    def fetch(self, url: str, silent: bool = False) -> requests.Response | None:
        try:
            resp = self.session.get(
                url, timeout=self.config["timeout"],
                stream=True, allow_redirects=True,
            )
            resp.raise_for_status()
            return resp
        except requests.HTTPError as e:
            code = e.response.status_code if e.response else "?"
            if not silent:
                self.log(f"  [✗] HTTP {code}: {url[:80]}")
            with self._fail_lock:
                self.failed.append(url)
        except requests.RequestException as e:
            if not silent:
                self.log(f"  [✗] {type(e).__name__}: {url[:80]}")
            with self._fail_lock:
                self.failed.append(url)
        return None

    # ── Simpan ────────────────────────────────────────────────────────────────

    def save_file(self, url: str, content, is_html=False, is_css=False):
        fp = url_to_filepath(url, self.output_dir)
        Path(fp).parent.mkdir(parents=True, exist_ok=True)

        try:
            if is_html and isinstance(content, str):
                data = rewrite_html(content, url, self.output_dir, self.max_url)
                with open(fp, "w", encoding="utf-8", errors="replace") as f:
                    f.write(data)
            elif is_css and isinstance(content, str):
                data = rewrite_css_urls(content, url, self.output_dir, self.max_url)
                with open(fp, "w", encoding="utf-8", errors="replace") as f:
                    f.write(data)
            elif isinstance(content, bytes):
                with open(fp, "wb") as f:
                    f.write(content)
            else:
                with open(fp, "w", encoding="utf-8", errors="replace") as f:
                    f.write(content)

            with self._dl_lock:
                self.downloaded.append(fp)
        except OSError as e:
            self.log(f"  [!] Gagal simpan {fp}: {e}")

    # ── Extract links ─────────────────────────────────────────────────────────

    def extract_links(self, html: str, page_url: str) -> set[str]:
        soup = BeautifulSoup(html, "html.parser")
        links: set[str] = set()

        for tag, attrs in URL_TAG_ATTRS.items():
            for el in soup.find_all(tag):
                for attr in attrs:
                    val = el.get(attr, "")
                    if not val:
                        continue
                    raw_list = extract_srcset_urls(val) if attr == "srcset" else [val]
                    for raw in raw_list:
                        u = normalize_url(raw, page_url, self.max_url)
                        if u:
                            links.add(u)

        for el in soup.find_all("meta"):
            prop = (el.get("property") or el.get("name") or "").lower().strip()
            if prop not in META_URL_PROPERTIES:
                continue
            val = el.get("content", "")
            u = normalize_url(val, page_url, self.max_url)
            if u:
                links.add(u)

        for style_el in soup.find_all("style"):
            if style_el.string:
                for m in re.finditer(r'url\(\s*["\']?([^)"\']+?)["\']?\s*\)', style_el.string):
                    u = normalize_url(m.group(1), page_url, self.max_url)
                    if u:
                        links.add(u)

        # Ekstrak juga URL dari dalam JavaScript (data-* attrs, JS strings)
        for el in soup.find_all(attrs={"data-url": True}):
            u = normalize_url(el["data-url"], page_url, self.max_url)
            if u: links.add(u)
        for el in soup.find_all(attrs={"data-src": True}):
            u = normalize_url(el["data-src"], page_url, self.max_url)
            if u: links.add(u)
        for el in soup.find_all(attrs={"data-href": True}):
            u = normalize_url(el["data-href"], page_url, self.max_url)
            if u: links.add(u)
        for el in soup.find_all(attrs={"data-bg": True}):
            u = normalize_url(el["data-bg"], page_url, self.max_url)
            if u: links.add(u)

        return links

    def is_same_domain(self, url: str) -> bool:
        return urllib.parse.urlparse(url).netloc == self.base_domain

    def is_asset(self, url: str) -> bool:
        ext = os.path.splitext(urllib.parse.urlparse(url).path)[1].lower()
        return ext in ASSET_EXTENSIONS

    # ── Proses satu URL ───────────────────────────────────────────────────────

    def _process_url(self, url: str, depth: int) -> list[tuple[str, int]]:
        """Fetch & simpan satu URL. Return list link baru untuk di-queue."""
        resp = self.fetch(url)
        if resp is None:
            return []

        ct = resp.headers.get("content-type", "")
        new_links = []

        if "text/html" in ct:
            html_text = resp.text
            self.save_file(url, html_text, is_html=True)
            if depth < self.config["max_depth"]:
                for link in self.extract_links(html_text, url):
                    with self._visited_lock:
                        if link not in self.visited:
                            new_links.append((link, depth + 1))

        elif "text/css" in ct:
            css_text = resp.text
            self.save_file(url, css_text, is_css=True)
            if depth < self.config["max_depth"]:
                for m in re.finditer(r'url\(\s*["\']?([^)"\']+?)["\']?\s*\)', css_text):
                    u = normalize_url(m.group(1), url, self.max_url)
                    if u:
                        with self._visited_lock:
                            if u not in self.visited:
                                new_links.append((u, depth + 1))
        else:
            self.save_file(url, resp.content)

        return new_links

    # ── CRAWL NORMAL ──────────────────────────────────────────────────────────

    def crawl(self):
        self.log(f"\n{'═'*65}")
        self.log(f"  🌐  Web Cloner  —  {self.start_url}")
        self.log(f"{'═'*65}")
        self.log(f"  Output     : {self.output_dir}")
        self.log(f"  Domain     : {self.base_domain}")
        self.log(f"  Max Depth  : {self.config['max_depth']}")
        self.log(f"  Max Pages  : {self.config['max_pages']}")
        self.log(f"  Bruteforce : {'✅ ON' if self.config['bruteforce'] else '❌ OFF'}")
        self.log(f"{'─'*65}\n")

        if self.config["respect_robots"]:
            self.load_robots()

        self.queue.append((self.start_url, 0))

        while self.queue:
            url, depth = self.queue.popleft()

            if not is_valid_url_string(url, self.max_url):
                continue
            with self._visited_lock:
                if url in self.visited:
                    continue
                self.visited.add(url)

            if self.config["same_domain_only"] and not self.is_same_domain(url):
                continue
            if not self.is_allowed(url):
                if self.is_same_domain(url):
                    self.log(f"  [robots] Diblokir: {url[:80]}")
                continue

            is_asset = self.is_asset(url)
            if not is_asset:
                with self._page_lock:
                    if self._page_count >= self.config["max_pages"]:
                        self.log(f"\n  [!] Batas {self.config['max_pages']} halaman tercapai.")
                        break
                    self._page_count += 1
                    pc = self._page_count

            label = "A" if is_asset else str(pc if not is_asset else 0)
            self.log(f"  [{label:>4}] (d={depth}) {url[:90]}")

            new_links = self._process_url(url, depth)
            for link, d in new_links:
                self.queue.append((link, d))

            time.sleep(self.config["delay"])

    # ── BRUTEFORCE MODE ───────────────────────────────────────────────────────

    def bruteforce(self):
        """
        Coba semua path di BRUTEFORCE_PATHS secara paralel.
        Juga scan direktori listing jika aktif.
        """
        self.log(f"\n{'═'*65}")
        self.log(f"  🔍  BRUTEFORCE PATH SCAN  —  {self.base_origin}")
        self.log(f"{'═'*65}")
        self.log(f"  Total path yang dicoba : {len(BRUTEFORCE_PATHS)}")
        self.log(f"  Thread paralel         : {self.config['bf_threads']}")
        self.log(f"{'─'*65}\n")

        found      = []
        found_lock = threading.Lock()
        counter    = [0]
        c_lock     = threading.Lock()

        def probe(path: str):
            url = self.base_origin + path
            with self._visited_lock:
                if url in self.visited:
                    return
            try:
                resp = self.session.get(
                    url,
                    timeout=self.config["timeout"],
                    allow_redirects=True,
                    stream=True,
                )
                with c_lock:
                    counter[0] += 1
                    n = counter[0]

                if resp.status_code == 200:
                    ct = resp.headers.get("content-type", "")
                    size = int(resp.headers.get("content-length", 0))
                    size_str = f"{size/1024:.1f} KB" if size else "?"

                    self.log(f"  [BF {n:>4}] ✅ {resp.status_code}  {url:<60}  [{size_str}]")

                    with self._visited_lock:
                        self.visited.add(url)

                    with found_lock:
                        found.append(url)

                    # Simpan file
                    if "text/html" in ct:
                        self.save_file(url, resp.text, is_html=True)
                        # Ekstrak link baru dari halaman yang ditemukan
                        new_links = self.extract_links(resp.text, url)
                        for link in new_links:
                            with self._visited_lock:
                                already = link in self.visited
                            if not already and self.is_same_domain(link):
                                self.queue.append((link, 99))  # depth 99 = dari BF

                    elif "text/css" in ct:
                        self.save_file(url, resp.text, is_css=True)
                    else:
                        self.save_file(url, resp.content)

                    # Kalau direktori listing terbuka, parse filenya juga
                    if "text/html" in ct and path.endswith("/"):
                        self._parse_directory_listing(resp.text, url)

                elif resp.status_code not in (404, 403, 410):
                    # Status menarik (301, 302, 401, dll.)
                    self.log(f"  [BF {n:>4}] ⚠️  {resp.status_code}  {url[:70]}")

            except requests.RequestException:
                pass  # Silent untuk bruteforce
            finally:
                time.sleep(self.config["bf_delay"])

        with ThreadPoolExecutor(max_workers=self.config["bf_threads"]) as executor:
            futures = [executor.submit(probe, path) for path in BRUTEFORCE_PATHS]
            try:
                for f in as_completed(futures):
                    f.result()
            except KeyboardInterrupt:
                executor.shutdown(wait=False, cancel_futures=True)
                raise

        self.log(f"\n  {'─'*60}")
        self.log(f"  🔍 Bruteforce selesai: {len(found)} path ditemukan dari {len(BRUTEFORCE_PATHS)} dicoba")

        # Lanjut crawl link baru yang ditemukan dari BF
        if self.queue:
            self.log(f"  🔗 Crawl {len(self.queue)} link baru dari hasil BF...\n")
            self._crawl_remaining()

    def _parse_directory_listing(self, html: str, dir_url: str):
        """Parse Apache/Nginx directory listing — ambil semua file di dalamnya."""
        soup = BeautifulSoup(html, "html.parser")
        count = 0
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href in ("..", "./", "/", "#"):
                continue
            if href.startswith("?"):  # sort parameter Apache
                continue
            full_url = urllib.parse.urljoin(dir_url, href)
            if not self.is_same_domain(full_url):
                continue
            with self._visited_lock:
                already = full_url in self.visited
            if not already:
                self.queue.append((full_url, 98))
                count += 1
        if count:
            self.log(f"  [DIR] 📂 {dir_url}  →  {count} file/subdir ditemukan")

    def _crawl_remaining(self):
        """Crawl sisa queue (dari hasil bruteforce)."""
        while self.queue:
            url, depth = self.queue.popleft()
            if not is_valid_url_string(url, self.max_url):
                continue
            with self._visited_lock:
                if url in self.visited:
                    continue
                self.visited.add(url)
            if self.config["same_domain_only"] and not self.is_same_domain(url):
                continue

            is_asset = self.is_asset(url)
            label = "A" if is_asset else "BF"
            self.log(f"  [{label:>4}]        {url[:90]}")

            new_links = self._process_url(url, depth)
            for link, d in new_links:
                with self._visited_lock:
                    already = link in self.visited
                if not already:
                    self.queue.append((link, d))

            time.sleep(self.config["delay"])

    # ── Finalisasi ────────────────────────────────────────────────────────────

    def finalize(self):
        site_dir = os.path.join(self.output_dir, self.base_domain)
        total_size = sum(
            os.path.getsize(f) for f in self.downloaded if os.path.exists(f)
        )
        self.log(f"\n{'─'*65}")
        self.log(f"  ✅  {len(self.downloaded)} file tersimpan  ({total_size/1024/1024:.2f} MB)")
        self.log(f"  📁  Lokasi: {site_dir}")
        if self.failed:
            self.log(f"  ⚠️   {len(self.failed)} URL gagal")

        if self.config["create_zip"]:
            zip_path = site_dir + ".zip"
            self.log(f"  📦  Membuat ZIP → {zip_path} ...")
            zip_output(site_dir, zip_path)
            size_mb = os.path.getsize(zip_path) / 1024 / 1024
            self.log(f"  ✅  ZIP selesai  ({size_mb:.2f} MB)")

        self.log(f"{'═'*65}\n")


# ─── CLI ──────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(
        description="Web Cloner + Path Bruteforce — backup seluruh website",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Contoh:
  # Crawl biasa
  python web_cloner.py https://mysite.com

  # Aktifkan bruteforce (coba ~200 path umum)
  python web_cloner.py https://mysite.com --bruteforce

  # BF dengan thread lebih banyak & tanpa ZIP
  python web_cloner.py https://mysite.com --bruteforce --bf-threads 20 --no-zip

  # Crawl dalam + BF
  python web_cloner.py https://mysite.com --depth 5 --pages 1000 --bruteforce
        """,
    )
    p.add_argument("url")
    p.add_argument("--depth",       "-d",  type=int,   default=DEFAULT_CONFIG["max_depth"],
                   help=f"Kedalaman crawl (default: {DEFAULT_CONFIG['max_depth']})")
    p.add_argument("--pages",       "-p",  type=int,   default=DEFAULT_CONFIG["max_pages"],
                   help=f"Batas halaman (default: {DEFAULT_CONFIG['max_pages']})")
    p.add_argument("--delay",              type=float, default=DEFAULT_CONFIG["delay"],
                   help=f"Jeda per request (default: {DEFAULT_CONFIG['delay']}s)")
    p.add_argument("--timeout",            type=int,   default=DEFAULT_CONFIG["timeout"],
                   help=f"Timeout (default: {DEFAULT_CONFIG['timeout']}s)")
    p.add_argument("--output",      "-o",              default=DEFAULT_CONFIG["output_dir"],
                   help="Folder output (default: output)")
    p.add_argument("--no-zip",             action="store_true",
                   help="Jangan buat ZIP")
    p.add_argument("--no-robots",          action="store_true",
                   help="Abaikan robots.txt (default: sudah abaikan)")
    p.add_argument("--allow-external",     action="store_true",
                   help="Download aset dari domain lain juga")
    p.add_argument("--max-url",            type=int,   default=DEFAULT_CONFIG["max_url_length"],
                   help="Batas panjang URL (default: 500)")
    p.add_argument("--bruteforce",  "-b",  action="store_true",
                   help="🔍 Aktifkan path bruteforce (~200 path umum)")
    p.add_argument("--bf-threads",         type=int,   default=DEFAULT_CONFIG["bf_threads"],
                   help=f"Thread paralel bruteforce (default: {DEFAULT_CONFIG['bf_threads']})")
    p.add_argument("--bf-delay",           type=float, default=DEFAULT_CONFIG["bf_delay"],
                   help=f"Jeda per request BF (default: {DEFAULT_CONFIG['bf_delay']}s)")
    p.add_argument("--bf-only",            action="store_true",
                   help="Hanya jalankan bruteforce, skip crawl normal")
    p.add_argument("--user-agent",         default=DEFAULT_CONFIG["user_agent"])
    return p.parse_args()


def main():
    args = parse_args()
    url = args.url
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    config = {
        "max_depth":        args.depth,
        "max_pages":        args.pages,
        "delay":            args.delay,
        "timeout":          args.timeout,
        "user_agent":       args.user_agent,
        "output_dir":       args.output,
        "create_zip":       not args.no_zip,
        "respect_robots":   not args.no_robots,
        "same_domain_only": not args.allow_external,
        "max_url_length":   args.max_url,
        "bruteforce":       args.bruteforce or args.bf_only,
        "bf_threads":       args.bf_threads,
        "bf_delay":         args.bf_delay,
    }

    cloner = WebCloner(url, config)
    try:
        if not args.bf_only:
            cloner.crawl()
        if config["bruteforce"]:
            cloner.bruteforce()
        cloner.finalize()
    except KeyboardInterrupt:
        print("\n\n  [!] Dihentikan (Ctrl+C)")
        cloner.finalize()


if __name__ == "__main__":
    main()
