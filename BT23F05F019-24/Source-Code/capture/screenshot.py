"""Stage 1 — capture a live page as a screenshot plus its DOM.

Two deliberate constraints, both from the project's ethics section:

  * robots.txt is honoured. If a site disallows the path, we refuse rather than
    capture it.
  * A minimum interval is enforced between captures of the same host.

Only public pages. Never sign in, never complete a purchase, never capture a page
reached through authentication.
"""

from __future__ import annotations

import time
import urllib.robotparser
from urllib.parse import urlparse

USER_AGENT = (
    "DarkPatternAuditor/1.0 (academic research project; "
    "respects robots.txt; contact via project README)"
)

MIN_INTERVAL_S = 3.0
_last_hit: dict[str, float] = {}


class CaptureError(RuntimeError):
    pass


def _check_robots(url: str) -> None:
    parts = urlparse(url)
    if parts.scheme not in ("http", "https"):
        raise CaptureError(f"Only http(s) URLs are supported, got {parts.scheme!r}.")

    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(f"{parts.scheme}://{parts.netloc}/robots.txt")
    try:
        rp.read()
    except Exception:
        # No reachable robots.txt is not permission to ignore one that exists, but
        # it is also not a prohibition. Proceed, politely.
        return
    if not rp.can_fetch(USER_AGENT, url):
        raise CaptureError(
            "robots.txt disallows fetching this URL. Capture the screenshot manually "
            "in your own browser and upload it instead."
        )


def _rate_limit(host: str) -> None:
    last = _last_hit.get(host)
    if last is not None:
        wait = MIN_INTERVAL_S - (time.monotonic() - last)
        if wait > 0:
            time.sleep(wait)
    _last_hit[host] = time.monotonic()


def capture(
    url: str,
    *,
    full_page: bool = True,
    viewport: tuple[int, int] = (1366, 900),
    wait_ms: int = 2500,
) -> tuple[bytes, str]:
    """Return (png_bytes, html) for a public URL.

    `wait_ms` exists because the patterns we care about — cookie walls, upsell
    modals, countdowns — are usually injected after first paint. Capturing too
    early misses exactly the elements we are looking for.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:  # pragma: no cover
        raise CaptureError(
            "Playwright is not installed. Run:\n"
            "  pip install -r requirements.txt\n"
            "  playwright install chromium"
        ) from exc

    _check_robots(url)
    _rate_limit(urlparse(url).netloc)

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        try:
            page = browser.new_context(
                viewport={"width": viewport[0], "height": viewport[1]},
                user_agent=USER_AGENT,
            ).new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            page.wait_for_timeout(wait_ms)

            html = page.content()
            png = page.screenshot(full_page=full_page)
        except Exception as exc:
            raise CaptureError(f"Could not capture {url}: {exc}") from exc
        finally:
            browser.close()

    return png, html


# TODO (future scope): capture the same URL twice and diff any countdown text.
# A timer that resets between loads is proof of false urgency rather than a
# guess — but that is flow-level auditing, which this version keeps out of scope.
