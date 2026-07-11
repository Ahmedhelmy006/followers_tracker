"""
Instagram Service.

Retrieves follower counts for one or more Instagram profiles by intercepting
Instagram's own GraphQL responses through a proxied headless browser.
"""

import os, time, logging
from typing import Dict, Any, List, Optional
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class InstagramService:
    """
    Service for retrieving Instagram follower counts.

    Can be used for a single username (get_followers) or several usernames
    in one browser session (get_followers_bulk), which is cheaper than
    launching a fresh browser per profile.
    """

    def __init__(self, username: Optional[str] = None):
        """
        Args:
            username: Default Instagram username. Optional if you only
                      use get_followers_bulk() with explicit usernames.
        """
        self.username = username

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
        """
        results: Dict[str, Dict[str, Any]] = {}

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
                proxy={
                    "server": os.getenv("INSTAGRAM_PROXY_ADDRESS"),
                    "username": os.getenv("INSTAGRAM_PROXY_USERNAME"),
                    "password": os.getenv("INSTAGRAM_PROXY_PASSWORD"),
                },
            )
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0"
                )
            )

            for username in usernames:
                results[username] = self._fetch_profile(context, username)
                # Small pause between profiles to look less bot-like
                time.sleep(3)

            browser.close()

        return results

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #

    def _fetch_profile(self, context, username: str) -> Dict[str, Any]:
        """Visit one profile page and intercept its GraphQL follower count."""
        follower_count = {"value": None}
        page = context.new_page()

        def handle_response(response):
            if "graphql" in response.url and response.status == 200:
                try:
                    data = response.json()
                    user = data.get("data", {}).get("user", {})
                    if "follower_count" in user:
                        follower_count["value"] = user["follower_count"]
                        logger.info(f"[{username}] Follower count: {follower_count['value']}")
                except Exception as e:
                    logger.warning(f"[{username}] Could not parse response: {e}")

        page.on("response", handle_response)

        try:
            page.goto(
                f"https://www.instagram.com/{username}/",
                wait_until="networkidle",
                timeout=30000,
            )
        except Exception as e:
            logger.error(f"[{username}] Navigation error: {e}")
        finally:
            page.close()

        return {
            "platform": "Instagram",
            "username": username,
            "followers": follower_count["value"],
            "timestamp": time.time(),
            "source": "graphql_intercept",
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    service = InstagramService()
    result = service.get_followers_bulk(["nicolasboucherfinance", "theaifinanceclub"])
    print(result)