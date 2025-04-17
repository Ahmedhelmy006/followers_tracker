"""
Advanced LinkedIn Profile Service with enhanced anti-detection techniques.

This module handles retrieving follower counts from LinkedIn personal profiles
using stealth techniques to avoid sign-in pages and blocks.
"""

import re
import time
import logging
import random
from typing import Optional, Dict, Any, List
import os
import sys

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.settings import NICOLAS_LKD_PROFILE
from utils.playwright_stealth_driver import PlaywrightStealthDriver
from utils.exceptions import ScrapingError

logger = logging.getLogger(__name__)

class LinkedInProfileAdvancedService:
    """
    Advanced service for retrieving data from LinkedIn personal profiles.
    
    This service uses enhanced stealth techniques to avoid detection and
    extract follower counts from LinkedIn profile pages.
    """
    
    def __init__(self, profile_url: str = NICOLAS_LKD_PROFILE, proxies: Optional[List[str]] = None):
        """
        Initialize the LinkedIn Profile Advanced Service.
        
        Args:
            profile_url: URL of the LinkedIn profile to scrape, defaults to configured URL
            proxies: Optional list of proxy servers to use for rotation
        """
        self.profile_url = profile_url
        self.proxies = proxies or []
        logger.info(f"LinkedIn Profile Advanced Service initialized for URL: {profile_url}")
        
        # Add different URL variants to try if the main one fails
        self.url_variants = [
            profile_url,
            f"{profile_url}/",
            f"{profile_url}/details/recent-activity/",
            f"{profile_url}/about/",
        ]
    
    def get_followers(self) -> Optional[int]:
        """
        Get the number of followers for the LinkedIn profile using advanced techniques.
        
        Returns:
            The number of followers as an integer, or None if not found.
            
        Raises:
            ScrapingError: If there is an error during the scraping process.
        """
        max_attempts = 5
        attempt = 0
        
        while attempt < max_attempts:
            attempt += 1
            
            # Choose proxy if available
            proxy = None
            if self.proxies:
                proxy = random.choice(self.proxies)
                logger.info(f"Using proxy for attempt {attempt}: {proxy.split('@')[-1] if '@' in proxy else proxy}")
            
            # Create new stealth driver
            driver = PlaywrightStealthDriver(proxy=proxy)
            
            try:
                # Choose a URL variant to try
                url_to_try = random.choice(self.url_variants)
                
                # Initialize browser with stealth mode
                context = driver.initialize_driver(stealth_mode=True)
                
                # Create page with human-like behavior
                page, errors_detected = driver.create_page_with_wait(context)
                
                # Emulate human-like navigation
                self._emulate_human_navigation(page)
                
                # Navigate to profile page with randomized timing
                logger.info(f"Navigating to LinkedIn profile (attempt {attempt}/{max_attempts}): {url_to_try}")
                
                # Random pre-navigation delay (0.5 to 1.5 seconds)
                time.sleep(random.uniform(0.5, 1.5))
                
                # Navigate with extended timeout
                page.goto(url_to_try, timeout=90000)  # 90 seconds timeout
                
                # Random post-navigation delay (1 to 3 seconds)
                time.sleep(random.uniform(1, 3))
                
                # Scroll the page like a human would
                self._scroll_like_human(page)
                
                # Check if we got a sign-in page
                page_content = page.content()
                page_title = page.title()
                
                # LinkedIn sign-in page detection
                if any(phrase in page_content for phrase in ["Sign in to LinkedIn", "Join to view full profile", "Please log in", "Join now to see all activity"]):
                    logger.warning(f"Detected LinkedIn sign-in page on attempt {attempt}")
                    
                    # Close current context before retry
                    driver.close(context)
                    
                    # Exponential backoff with jitter
                    delay = (2 ** attempt) + random.uniform(1, 5)
                    logger.info(f"Waiting {delay:.2f} seconds before retry...")
                    time.sleep(delay)
                    continue
                
                # Try multiple extraction strategies
                followers = None
                
                # Strategy 1: Direct extraction from page content
                followers = self._extract_followers_from_content(page_content)
                
                # Strategy 2: If that fails, try extracting from page.evaluate
                if followers is None:
                    followers = self._extract_followers_from_javascript(page)
                
                # Strategy 3: If both fail, try scraping specific elements
                if followers is None:
                    followers = self._extract_followers_from_elements(page)
                
                if followers is not None:
                    logger.info(f"Successfully extracted follower count: {followers}")
                    driver.close(context)
                    return followers
                
                # If we reached here, we couldn't find followers with any strategy
                logger.warning(f"Could not find follower count on attempt {attempt}")
                
                # Close current context before retry
                driver.close(context)
                
                # Exponential backoff with jitter
                delay = (2 ** attempt) + random.uniform(1, 5)
                logger.info(f"Waiting {delay:.2f} seconds before retry...")
                time.sleep(delay)
                
            except Exception as e:
                error_msg = f"Error scraping LinkedIn profile (attempt {attempt}): {str(e)}"
                logger.error(error_msg)
                
                # Clean up resources
                if 'context' in locals():
                    driver.close(context)
                
                if attempt == max_attempts:
                    raise ScrapingError(error_msg)
                
                # Exponential backoff with jitter
                delay = (2 ** attempt) + random.uniform(1, 5)
                logger.info(f"Waiting {delay:.2f} seconds before retry...")
                time.sleep(delay)
        
        logger.error("Maximum retry attempts reached without finding follower count")
        return None
    
    def _emulate_human_navigation(self, page) -> None:
        """
        Emulate human-like navigation patterns.
        
        Args:
            page: Playwright page object
        """
        # Add random mouse movements
        if random.random() < 0.7:  # 70% chance
            try:
                # Move mouse to random positions
                page.mouse.move(
                    random.randint(100, 500),
                    random.randint(100, 500)
                )
                time.sleep(random.uniform(0.1, 0.3))
                
                page.mouse.move(
                    random.randint(200, 700),
                    random.randint(200, 700)
                )
            except Exception as e:
                logger.debug(f"Mouse movement error (non-critical): {str(e)}")
    
    def _scroll_like_human(self, page) -> None:
        """
        Scroll the page like a human would.
        
        Args:
            page: Playwright page object
        """
        try:
            # Get page height
            height = page.evaluate("() => document.body.scrollHeight")
            
            # Random number of scroll actions (2-5)
            scroll_actions = random.randint(2, 5)
            
            for i in range(scroll_actions):
                # Calculate random scroll amount
                scroll_amount = random.randint(300, 800)
                
                # Execute scroll
                page.evaluate(f"window.scrollBy(0, {scroll_amount})")
                
                # Random pause between scrolls
                time.sleep(random.uniform(0.5, 1.5))
                
                # Sometimes scroll back up a little
                if random.random() < 0.3:  # 30% chance
                    page.evaluate(f"window.scrollBy(0, -{random.randint(50, 200)})")
                    time.sleep(random.uniform(0.2, 0.7))
            
            # Final scroll to a random position
            if random.random() < 0.5:  # 50% chance to scroll to random position
                random_position = random.randint(height // 4, height // 2)
                page.evaluate(f"window.scrollTo(0, {random_position})")
                
        except Exception as e:
            logger.debug(f"Scroll error (non-critical): {str(e)}")
    
    def _extract_followers_from_content(self, page_content: str) -> Optional[int]:
        """
        Extract follower count from page content using regex.
        
        Args:
            page_content: HTML content of the LinkedIn profile page
            
        Returns:
            The number of followers as an integer, or None if not found
        """
        # Try multiple patterns for greater chance of success
        patterns = [
            # JSON data patterns
            r'"name":"Follows","userInteractionCount":(\d+)',
            r'followerCount":(\d+)',
            r'"followerCount":(\d+)',
            
            # HTML text patterns
            r'(\d+,?\d*)\s+followers',
            r'(\d+,?\d*)\s+Followers',
            r'>(\d+,?\d*)</span>\s*<span>followers',
            
            # Additional patterns for follower count
            r'follower[s]?" ?:? ?["\']?(\d+,?\d*)',
            r'connections?["\']?:(\d+,?\d*)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, page_content)
            if match:
                follower_text = match.group(1).replace(',', '')
                try:
                    return int(follower_text)
                except ValueError:
                    continue
        
        logger.debug("No regex patterns matched for follower count in page content")
        return None
    
    def _extract_followers_from_javascript(self, page) -> Optional[int]:
        """
        Extract follower count using JavaScript evaluation.
        
        Args:
            page: Playwright page object
            
        Returns:
            The number of followers as an integer, or None if not found
        """
        try:
            # Try to extract follower count from LinkedIn's internal data structure
            js_result = page.evaluate("""
            () => {
                // Look for data in window object
                if (window.__INITIAL_STATE__) {
                    return window.__INITIAL_STATE__;
                }
                
                // Look for JSON in script tags
                const scripts = document.querySelectorAll('script');
                let data = null;
                
                for (const script of scripts) {
                    if (script.textContent && script.textContent.includes('followerCount')) {
                        try {
                            const textContent = script.textContent;
                            const jsonStart = textContent.indexOf('{');
                            if (jsonStart >= 0) {
                                const jsonText = textContent.slice(jsonStart);
                                data = JSON.parse(jsonText);
                                break;
                            }
                        } catch (e) {
                            // continue to next script
                        }
                    }
                }
                
                return data;
            }
            """)
            
            if js_result:
                # Try to extract follower count from the data
                follower_count = None
                
                # Convert to string and search for patterns
                js_result_str = str(js_result)
                
                # Look for patterns in the string
                patterns = [
                    r'"followerCount":(\d+)',
                    r'"Follows","userInteractionCount":(\d+)',
                    r'"connectionCount":(\d+)'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, js_result_str)
                    if match:
                        follower_count = int(match.group(1))
                        break
                
                if follower_count:
                    return follower_count
        
        except Exception as e:
            logger.debug(f"JavaScript extraction error (non-critical): {str(e)}")
        
        return None
    
    def _extract_followers_from_elements(self, page) -> Optional[int]:
        """
        Extract follower count by targeting specific page elements.
        
        Args:
            page: Playwright page object
            
        Returns:
            The number of followers as an integer, or None if not found
        """
        try:
            # Try various selectors that might contain follower counts
            selectors = [
                "span.t-bold:has-text('followers')",
                "span.t-black--light:has-text('followers')",
                "span.inline-block:has-text('followers')",
                ".pv-top-card--list-bullet li.text-body-small",
                ".pvs-list__item--with-border span.t-black--light",
                "div:has-text('followers') span.t-bold",
                "[data-test-id='follower-count']",
                "span.link-without-visited-state--is-touched",
                "div.ph5 ul.mt2 li.inline-block",
                "ul.pv-top-card--list-bullet li"
            ]
            
            for selector in selectors:
                try:
                    elements = page.query_selector_all(selector)
                    
                    for element in elements:
                        text = element.inner_text()
                        if "follower" in text.lower():
                            # Extract numbers from text
                            match = re.search(r'(\d+[,\.]?\d*)', text)
                            if match:
                                follower_text = match.group(1).replace(',', '')
                                return int(follower_text)
                except Exception:
                    continue
                
        except Exception as e:
            logger.debug(f"Element extraction error (non-critical): {str(e)}")
        
        return None
    
    def get_profile_data(self) -> Dict[str, Any]:
        """
        Get all profile data including follower count.
        
        Returns:
            Dictionary containing profile data with follower count
        """
        followers = self.get_followers()
        
        return {
            "platform": "LinkedIn",
            "type": "Personal Profile",
            "url": self.profile_url,
            "followers": followers if followers is not None else "Not Found",
            "timestamp": time.time()
        }


if __name__ == "__main__":
    # Configure basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # List of proxies (replace with your actual proxies if available)
    # Format: "http://username:password@host:port"
    proxies = []
    
    # Create service and get data
    service = LinkedInProfileAdvancedService(proxies=proxies)
    profile_data = service.get_profile_data()
    
    # Print results
    print(f"LinkedIn Profile Data: {profile_data}")