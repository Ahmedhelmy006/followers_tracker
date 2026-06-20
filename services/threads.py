"""
Threads Profile Service.

This module handles retrieving follower counts from Threads personal profiles.
It uses regex pattern matching to extract data from the HTML response.
"""

import re
import time
import logging
from typing import Optional, Dict, Any
import os, sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.playwright_driver import PlaywrightDriver
from utils.exceptions import ScrapingError

logger = logging.getLogger(__name__)


class ThreadsProfileService:
    """
    Service for retrieving data from Threads personal profiles.

    This service extracts follower counts using regex pattern matching
    from the HTML of Threads profile pages.
    """

    def __init__(self, profile_url: str = 'https://www.threads.com/@nicolasboucherfinance', max_retries: int = 5, retry_wait_seconds: int = 10):
        """
        Initialize the Threads Profile Service.

        Args:
            profile_url: URL of the Threads profile to scrape, defaults to configured URL
            max_retries: Maximum number of retry attempts if follower count is not found
            retry_wait_seconds: Wait time in seconds between retry attempts
        """
        self.profile_url = profile_url
        self.max_retries = max_retries
        self.retry_wait_seconds = retry_wait_seconds
        logger.info(f"Threads Profile Service initialized for URL: {profile_url}")

    def get_followers(self) -> Optional[int]:
        """
        Get the number of followers for the Threads profile.

        Returns:
            The number of followers as an integer, or None if not found.

        Raises:
            ScrapingError: If there is an error during the scraping process.
        """
        retries = 0

        while retries <= self.max_retries:
            driver = PlaywrightDriver()
            context = None

            try:
                context = driver.initialize_driver()
                page = context.new_page()

                logger.info(f"Navigating to Threads profile: {self.profile_url} (Attempt {retries + 1}/{self.max_retries + 1})")
                page.goto(self.profile_url, timeout=120000)

                logger.debug("Waiting for page content to load")
                time.sleep(3)

                page_content = page.content()

                followers = self._extract_followers(page_content)

                if followers is not None:
                    logger.info(f"Successfully extracted follower count: {followers}")
                    driver.close(context)
                    return followers

                logger.warning(f"Could not find follower count (Attempt {retries + 1}/{self.max_retries + 1})")

                driver.close(context)

                if retries == self.max_retries:
                    logger.warning(f"Could not find follower count after {retries + 1} attempts")
                    return None

                retries += 1
                logger.info(f"Retrying in {self.retry_wait_seconds} seconds (Attempt {retries + 1}/{self.max_retries + 1})")
                time.sleep(self.retry_wait_seconds)

            except Exception as e:
                error_msg = f"Error scraping Threads profile: {str(e)}"
                logger.error(error_msg)

                if context:
                    driver.close(context)

                if retries == self.max_retries:
                    raise ScrapingError(error_msg)

                retries += 1
                logger.info(f"Error occurred. Retrying in {self.retry_wait_seconds} seconds (Attempt {retries + 1}/{self.max_retries + 1})")
                time.sleep(self.retry_wait_seconds)

        return None

    def _extract_followers(self, page_content: str) -> Optional[int]:
        """
        Extract follower count from page content using regex.

        Args:
            page_content: HTML content of the Threads profile page

        Returns:
            The number of followers as an integer, or None if not found
        """
        # Primary pattern — embedded JSON in script tags
        primary_match = re.search(r'"follower_count"\s*:\s*(\d+)', page_content)
        if primary_match:
            return int(primary_match.group(1))

        # Fallback — older or alternate JSON key
        fallback_match = re.search(r'"followerCount"\s*:\s*(\d+)', page_content)
        if fallback_match:
            return int(fallback_match.group(1))

        # Second fallback — rendered text (e.g. "2,133 followers")
        text_match = re.search(r'([\d,]+)\s+followers', page_content)
        if text_match:
            return int(text_match.group(1).replace(',', ''))

        logger.debug("No regex patterns matched for follower count")
        return None

    def get_profile_data(self) -> Dict[str, Any]:
        """
        Get all profile data including follower count.

        Returns:
            Dictionary containing profile data with follower count
        """
        followers = self.get_followers()

        return {
            "platform": "Threads",
            "type": "Personal Profile",
            "url": self.profile_url,
            "followers": followers if followers is not None else "Not Found",
            "timestamp": time.time()
        }


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    service = ThreadsProfileService()
    profile_data = service.get_profile_data()

    print(f"Threads Profile Data: {profile_data}")