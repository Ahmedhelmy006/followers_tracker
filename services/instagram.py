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
configured by SOCIALBLADE_COOKIES_FILE. Socialblade sits behind Cloudflare, so
the FIRST navigation in a cold context can be met with a 403 challenge page;
we warm the context up with a throwaway homepage hit and retry each profile a
couple of times to ride through that.
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
from playwright.sync_api import sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from config.settings import (
    INSTAGRAM_USERNAME,
    SOCIALBLADE_COOKIES_FILE,
    SOCIALBLADE_HEADLESS,
    SOCIALBLADE_TIMEOUT_MS,
)

logger = logging.getLogger(__name__)

HOME_URL = "https://socialblade.com/"
URL_TEMPLATE = "https://socialblade.com/instagram/search?query={handle}"

# How many times to attempt a single profile before giving up.
PROFILE_ATTEMPTS = 3
# Seconds to wait after a blocked attempt before retrying (Cloudflare clearance
# usually lands within a second or two of the challenge being solved).
RETRY_WAIT_SECONDS = 4

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

                # Warm the context up so the Cloudflare challenge is cleared
                # BEFORE the first real profile fetch (otherwise the first
                # profile in the batch eats the 403 challenge page).
                self._warm_up(context)

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

    def _warm_up(self, context) -> None:
        """
        Prime the context against Cloudflare by hitting the homepage once.

        A cold context often gets a 403 challenge on its first navigation;
        Chromium solves the JS challenge and Cloudflare drops a fresh
        clearance cookie into the context. Spending that challenge on a
        throwaway homepage hit means the profile fetches that follow start
        already cleared. Best-effort: failures here are non-fatal.
        """
        page = context.new_page()
        try:
            resp = page.goto(HOME_URL, wait_until="domcontentloaded", timeout=SOCIALBLADE_TIMEOUT_MS)
            status = resp.status if resp else "unknown"
            logger.info(f"Socialblade warm-up hit homepage (HTTP {status})")
            # Give any challenge redirect a moment to settle and set clearance.
            time.sleep(3)
        except Exception as e:
            logger.warning(f"Socialblade warm-up navigation failed (continuing anyway): {e}")
        finally:
            page.close()

    def _fetch_profile(self, context, username: str) -> Dict[str, Any]:
        """
        Load one Socialblade search page and pull the live follower count,
        retrying through transient Cloudflare blocks.
        """
        for attempt in range(1, PROFILE_ATTEMPTS + 1):
            try:
                html, status = self._fetch_html(context, username)

                if status is not None and status != 200:
                    logger.warning(
                        f"[{username}] Socialblade returned HTTP {status} "
                        f"(attempt {attempt}/{PROFILE_ATTEMPTS})"
                    )
                    if self._retry_pause(attempt):
                        continue
                    return self._result(username, None)

                data = self._extract_next_data(html)
                platform_result = self._find_platform_result(data)

                if platform_result is None:
                    # An expired session returns 200 with logged-out HTML, not
                    # an error; a challenge page also lands here with no data.
                    logger.warning(
                        f"[{username}] No platformResult in payload "
                        f"(attempt {attempt}/{PROFILE_ATTEMPTS}). Handle may not "
                        "exist, the page was a challenge, or the session cookie expired."
                    )
                    if self._retry_pause(attempt):
                        continue
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
                logger.warning(
                    f"[{username}] Fetch failed (attempt {attempt}/{PROFILE_ATTEMPTS}): {e}"
                )
                if self._retry_pause(attempt):
                    continue
                logger.error(f"[{username}] Giving up after {PROFILE_ATTEMPTS} attempts")
                return self._result(username, None)

        return self._result(username, None)

    @staticmethod
    def _retry_pause(attempt: int) -> bool:
        """Sleep before a retry. Returns True if another attempt remains."""
        if attempt < PROFILE_ATTEMPTS:
            time.sleep(RETRY_WAIT_SECONDS)
            return True
        return False

    def _fetch_html(self, context, handle: str) -> tuple:
        """
        Load the search page in a fresh tab and return (html, status).

        We read the status from the navigation response and the markup from
        page.content() (the serialized live DOM, which contains __NEXT_DATA__).
        This avoids reading response.body() inside an event handler, which
        races page teardown and throws TargetClosedError.
        """
        target = URL_TEMPLATE.format(handle=handle)
        page = context.new_page()

        try:
            # NOT networkidle -- ad tags keep the connection count above zero
            # forever, so that condition can never be satisfied on this site.
            response = page.goto(target, wait_until="domcontentloaded", timeout=SOCIALBLADE_TIMEOUT_MS)
            status = response.status if response else None
            html = page.content()
            return html, status
        finally:
            page.close()

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