"""
Instagram Service.

Retrieves LIVE follower counts for one or more Instagram profiles by reading
Socialblade's /search endpoint, which embeds a `platformResult` object fetched
at request time.

Note on which page this hits: the /search endpoint carries `platformResult`,
which is live. The /user page carries a daily snapshot series instead (midnight
UTC), so it CANNOT produce the live number. If history is ever needed rather
than a live reading, that's the other page.

Requires a Socialblade cookie jar (Chrome-extension export format) at the path
configured by SOCIALBLADE_COOKIES_FILE. An expired session returns HTTP 200
with logged-out HTML, so failures surface as a missing `platformResult`.
"""

import os, sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from urllib.parse import urlsplit

from bs4 import BeautifulSoup
from playwright.sync_api import Response, sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from config.settings import (
    INSTAGRAM_USERNAME,
    SOCIALBLADE_COOKIES_FILE,
    SOCIALBLADE_HEADLESS,
    SOCIALBLADE_TIMEOUT_MS,
)

logger = logging.getLogger(__name__)

URL_TEMPLATE = "https://socialblade.com/instagram/search?query={handle}"

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

# Ad/analytics hosts that never stop making requests.
BLOCKED_HOSTS = (
    "doubleclick.net",
    "googlesyndication.com",
    "googletagservices.com",
    "googletagmanager.com",
    "google-analytics.com",
    "adservice.google.com",
    "adnxs.com",
    "amazon-adsystem.com",
    "criteo.com",
    "pubmatic.com",
    "rubiconproject.com",
    "casalemedia.com",
    "openx.net",
    "taboola.com",
    "outbrain.com",
    "scorecardresearch.com",
)

SAME_SITE_MAP = {
    "no_restriction": "None",
    "unspecified": "Lax",
    "lax": "Lax",
    "strict": "Strict",
}


class InstagramService:
    """
    Service for retrieving Instagram follower counts from Socialblade.

    Can be used for a single username (get_followers) or several usernames
    in one browser session (get_followers_bulk), which is cheaper than
    launching a fresh browser per profile.
    """

    def __init__(self, username: Optional[str] = None, cookies_file: Optional[str] = None):
        """
        Args:
            username: Default Instagram username. Optional if you only
                      use get_followers_bulk() with explicit usernames.
            cookies_file: Path to the Socialblade cookie jar. Defaults to
                          the path from settings.
        """
        self.username = username or INSTAGRAM_USERNAME
        self.cookies_file = Path(cookies_file or SOCIALBLADE_COOKIES_FILE)
        logger.info(f"Instagram Service initialized (source: socialblade, cookies: {self.cookies_file})")

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def get_followers(self, username: Optional[str] = None) -> Dict[str, Any]:
        """
        Get follower data for a single username.

        Args:
            username: Username to fetch. Falls back to the instance default.

        Returns:
            Dictionary containing follower data (followers is None on failure).
        """
        target = username or self.username
        if not target:
            raise ValueError("No Instagram username provided")

        results = self.get_followers_bulk([target])
        return results[target]

    def get_followers_bulk(self, usernames: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Get follower data for several usernames using ONE browser session.

        Args:
            usernames: List of Instagram usernames.

        Returns:
            Dict keyed by username, each value being the usual result dict.
            A failure for one profile does not abort the others.
        """
        results: Dict[str, Dict[str, Any]] = {}

        if not self.cookies_file.exists():
            logger.error(
                f"Socialblade cookie file not found at {self.cookies_file}. "
                "Cannot fetch Instagram follower counts."
            )
            return {u: self._result(u, None) for u in usernames}

        try:
            cookies = self._load_cookies(self.cookies_file)
        except Exception as e:
            logger.error(f"Failed to parse Socialblade cookies: {e}")
            return {u: self._result(u, None) for u in usernames}

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=SOCIALBLADE_HEADLESS,
                    args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
                )
                context = browser.new_context(
                    user_agent=UA,
                    viewport={"width": 1366, "height": 900},
                )
                context.add_cookies(cookies)
                context.route(
                    "**/*",
                    lambda route: route.abort()
                    if any(h in urlsplit(route.request.url).netloc for h in BLOCKED_HOSTS)
                    else route.continue_(),
                )

                try:
                    for i, username in enumerate(usernames):
                        results[username] = self._fetch_profile(context, username)
                        # Small pause between profiles to look less bot-like
                        if i < len(usernames) - 1:
                            time.sleep(3)
                finally:
                    browser.close()

        except Exception as e:
            logger.error(f"Socialblade browser session failed: {e}")
            for username in usernames:
                results.setdefault(username, self._result(username, None))

        return results

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #

    def _fetch_profile(self, context, username: str) -> Dict[str, Any]:
        """Load one Socialblade search page and pull the live follower count."""
        try:
            html, status = self._fetch_html(context, username)

            if status != 200:
                logger.warning(f"[{username}] Socialblade returned HTTP {status}")

            data = self._extract_next_data(html)
            platform_result = self._find_platform_result(data)

            if platform_result is None:
                # An expired session returns 200 with logged-out HTML, not an error.
                logger.error(
                    f"[{username}] No platformResult in payload. Either the handle "
                    "doesn't exist, or the Socialblade session cookie has expired "
                    "(it returns HTTP 200 either way)."
                )
                return self._result(username, None)

            followers = platform_result.get("followers")
            if followers is None:
                logger.error(
                    f"[{username}] platformResult has no 'followers'. Keys: {list(platform_result)}"
                )
                return self._result(username, None)

            # Comes back as int on some routes, str on others.
            followers = int(followers)
            logger.info(f"[{username}] Follower count: {followers}")
            return self._result(username, followers)

        except Exception as e:
            logger.error(f"[{username}] Failed to fetch follower count: {e}")
            return self._result(username, None)

    def _fetch_html(self, context, handle: str) -> tuple:
        """Load the search page in a fresh tab; return (html, status)."""
        target = URL_TEMPLATE.format(handle=handle)
        captured: dict = {}

        page = context.new_page()

        def on_response(response: Response) -> None:
            if self._normalize(response.url) != self._normalize(target):
                return
            if response.request.resource_type != "document":
                return
            captured["status"] = response.status
            captured["body"] = response.body()  # must be read before the page closes

        page.on("response", on_response)

        try:
            # NOT networkidle -- ad tags keep the connection count above zero
            # forever, so that condition can never be satisfied on this site.
            page.goto(target, wait_until="domcontentloaded", timeout=SOCIALBLADE_TIMEOUT_MS)
        except PlaywrightTimeoutError:
            # A nav timeout isn't a failure if the document already landed.
            if "body" not in captured:
                raise
            logger.debug(f"[{handle}] Nav timed out; document response already captured.")
        finally:
            page.close()

        if "body" not in captured:
            raise RuntimeError(f"No document response for {target} -- redirected or blocked?")

        return captured["body"].decode("utf-8", errors="replace"), captured["status"]

    @staticmethod
    def _load_cookies(path: Path) -> List[Dict[str, Any]]:
        """
        Translate a Chrome-extension cookie export into Playwright's schema.

        Differences that matter:
          - expirationDate -> expires; must be omitted for session cookies
          - sameSite is snake_case here, TitleCase in Playwright
          - hostOnly is expressed via the leading dot on domain
          - hostOnly/session/storeId have no equivalent and are rejected outright
        """
        raw = json.loads(path.read_text(encoding="utf-8"))
        cookies = []

        for c in raw:
            domain = c["domain"]
            if c.get("hostOnly") and domain.startswith("."):
                domain = domain.lstrip(".")
            elif not c.get("hostOnly") and not domain.startswith("."):
                domain = "." + domain

            cookie = {
                "name": c["name"],
                "value": c["value"],
                "domain": domain,
                "path": c.get("path", "/"),
                "httpOnly": bool(c.get("httpOnly", False)),
                "secure": bool(c.get("secure", False)),
            }

            same_site = c.get("sameSite")
            if same_site:
                cookie["sameSite"] = SAME_SITE_MAP.get(same_site.lower(), "Lax")

            if not c.get("session") and c.get("expirationDate"):
                cookie["expires"] = float(c["expirationDate"])

            cookies.append(cookie)

        return cookies

    @staticmethod
    def _normalize(url: str) -> str:
        """Compare URLs on scheme+host+path, ignoring query and fragment."""
        parts = urlsplit(url)
        return f"{parts.scheme}://{parts.netloc}{parts.path}".rstrip("/")

    @staticmethod
    def _extract_next_data(html: str) -> Dict[str, Any]:
        soup = BeautifulSoup(html, "html.parser")
        tag = soup.find("script", id="__NEXT_DATA__")
        if tag is None or not tag.string:
            raise RuntimeError("No __NEXT_DATA__ tag -- blocked, or the page changed.")
        return json.loads(tag.string)

    @classmethod
    def _find_platform_result(cls, node):
        """
        DFS for the first dict holding a 'platformResult' key.

        The tRPC queries array isn't stably ordered, so indexing into it by position
        is brittle. Walking the tree costs nothing at this payload size.
        """
        if isinstance(node, dict):
            if isinstance(node.get("platformResult"), dict):
                return node["platformResult"]
            for value in node.values():
                found = cls._find_platform_result(value)
                if found is not None:
                    return found
        elif isinstance(node, list):
            for item in node:
                found = cls._find_platform_result(item)
                if found is not None:
                    return found
        return None

    @staticmethod
    def _result(username: str, followers: Optional[int]) -> Dict[str, Any]:
        """Build the result dict the rest of the pipeline expects."""
        return {
            "platform": "Instagram",
            "username": username,
            "followers": followers,
            "timestamp": time.time(),
            "source": "socialblade_live",
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    service = InstagramService()
    result = service.get_followers_bulk(["nicolasboucherfinance", "theaifinanceclub"])
    print(result)