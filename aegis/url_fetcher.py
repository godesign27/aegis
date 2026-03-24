"""URL Fetcher — fetch a live webpage and extract auditable source files.

Given a URL, this module:
1. Fetches the raw HTML with httpx (async, with a browser-like User-Agent)
2. Parses the HTML to extract inline <style> and <script> blocks
3. Fetches linked external CSS/JS files (up to a reasonable limit)
4. Returns a dict of { filename: content } suitable for the Aegis parser

Design notes:
- Treats inline scripts/styles as files (e.g., "inline_script_1.js")
- External assets are fetched concurrently with a semaphore to avoid hammering
- Falls back gracefully if external assets are unreachable
- Respects a configurable timeout and asset count cap
"""
from __future__ import annotations

import logging
import re
from urllib.parse import urljoin, urlparse

import httpx

logger = logging.getLogger(__name__)

# Max external assets (CSS + JS) to fetch per URL audit
_MAX_EXTERNAL_ASSETS = 10
# Request timeout in seconds
_TIMEOUT = 15
# A realistic browser User-Agent to avoid bot blocks
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/123.0.0.0 Safari/537.36"
)

_LINK_CSS_RE = re.compile(
    r'<link[^>]+rel=["\']stylesheet["\'][^>]*href=["\']([^"\']+)["\']',
    re.IGNORECASE,
)
_LINK_CSS_ALT_RE = re.compile(
    r'<link[^>]+href=["\']([^"\']+\.css(?:\?[^"\']*)?)["\'][^>]*>',
    re.IGNORECASE,
)
_SCRIPT_SRC_RE = re.compile(
    r'<script[^>]+src=["\']([^"\']+)["\']',
    re.IGNORECASE,
)
_INLINE_STYLE_RE = re.compile(
    r'<style[^>]*>(.*?)</style>',
    re.IGNORECASE | re.DOTALL,
)
_INLINE_SCRIPT_RE = re.compile(
    r'<script(?![^>]*src)[^>]*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)


async def fetch_url_sources(url: str) -> dict[str, str]:
    """
    Fetch a URL and return a dict of { filename: content } for audit.

    The returned dict always includes:
      - "page.html": the raw HTML source
      - "inline_style_N.css": each <style> block
      - "inline_script_N.js": each non-empty inline <script> block
      - External CSS/JS files up to _MAX_EXTERNAL_ASSETS total

    Raises httpx.HTTPError if the main page fetch fails.
    """
    files: dict[str, str] = {}

    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=_TIMEOUT,
        headers={"User-Agent": _USER_AGENT},
    ) as client:
        # --- Fetch the main HTML page ---
        logger.info(f"Fetching URL: {url}")
        response = await client.get(url)
        response.raise_for_status()
        html = response.text
        files["page.html"] = html

        base_url = str(response.url)  # resolved URL after redirects

        # --- Extract inline styles ---
        for i, match in enumerate(
            _INLINE_STYLE_RE.finditer(html), start=1
        ):
            content = match.group(1).strip()
            if content:
                files[f"inline_style_{i}.css"] = content

        # --- Extract inline scripts ---
        inline_scripts = [
            m.group(1).strip()
            for m in _INLINE_SCRIPT_RE.finditer(html)
            if m.group(1).strip()
        ]
        for i, content in enumerate(inline_scripts, start=1):
            # Skip tiny/trivial scripts (analytics snippets, etc.)
            if len(content) > 100:
                files[f"inline_script_{i}.js"] = content

        # --- Collect external CSS/JS hrefs ---
        external_urls: list[tuple[str, str]] = []  # (absolute_url, filename)

        css_hrefs = _LINK_CSS_RE.findall(html) + _LINK_CSS_ALT_RE.findall(html)
        seen: set[str] = set()
        for href in css_hrefs:
            abs_url = urljoin(base_url, href)
            if abs_url not in seen:
                seen.add(abs_url)
                filename = _url_to_filename(abs_url, ".css")
                external_urls.append((abs_url, filename))

        js_srcs = _SCRIPT_SRC_RE.findall(html)
        for src in js_srcs:
            abs_url = urljoin(base_url, src)
            if abs_url not in seen and _is_same_origin_or_main(abs_url, base_url):
                seen.add(abs_url)
                filename = _url_to_filename(abs_url, ".js")
                external_urls.append((abs_url, filename))

        # Limit total external assets fetched
        external_urls = external_urls[:_MAX_EXTERNAL_ASSETS]

        # --- Fetch external assets concurrently ---
        import asyncio
        sem = asyncio.Semaphore(4)

        async def _fetch_one(abs_url: str, filename: str) -> tuple[str, str | None]:
            async with sem:
                try:
                    r = await client.get(abs_url)
                    r.raise_for_status()
                    return filename, r.text
                except Exception as exc:
                    logger.debug(f"Could not fetch external asset {abs_url}: {exc}")
                    return filename, None

        results = await asyncio.gather(
            *[_fetch_one(u, fn) for u, fn in external_urls]
        )
        for filename, content in results:
            if content and len(content) > 50:
                files[filename] = content

    logger.info(
        f"Fetched {len(files)} source files from {url}: {list(files.keys())[:8]}"
    )
    return files


def _url_to_filename(url: str, default_ext: str) -> str:
    """Convert a URL to a short readable filename."""
    parsed = urlparse(url)
    path = parsed.path.rstrip("/") or "index"
    # Take just the last two path segments to keep it short
    parts = [p for p in path.split("/") if p]
    name = "/".join(parts[-2:]) if len(parts) >= 2 else (parts[0] if parts else "file")
    # Strip query params, ensure extension
    name = name.split("?")[0]
    if not any(name.endswith(ext) for ext in (".css", ".js", ".ts", ".tsx", ".jsx")):
        name += default_ext
    return name


def _is_same_origin_or_main(url: str, base_url: str) -> bool:
    """Return True if the URL is from the same host as the base (avoid CDN spam)."""
    try:
        base_host = urlparse(base_url).netloc
        url_host = urlparse(url).netloc
        # Allow same origin or well-known asset CDNs
        return (
            url_host == base_host
            or "cdn." in url_host
            or url_host.endswith(".cloudflare.com")
        )
    except Exception:
        return False
