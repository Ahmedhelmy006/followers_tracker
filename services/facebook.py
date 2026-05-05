import re
import time
import logging
from typing import Optional, Dict, Any
import os, sys

from services.linkedin_profile import LinkedInProfileService

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from config.settings import FACEBOOK_URL
from utils.playwright_driver import PlaywrightDriver
from utils.exceptions import ScrapingError

logger = logging.getLogger(__name__)

class FacebookProfileService:
    def __init__(self, profile_url: str = FACEBOOK_URL, max_retries: int = 5, retry_wait_seconds: int = 10):
        """
        Initialize the Facebook Profile Service.
        
        Args:
            profile_url: URL of the Facebook profile to scrape, defaults to configured URL
            max_retries: Maximum number of retry attempts if follower count is not found
            retry_wait_seconds: Wait time in seconds between retry attempts
        """
        self.profile_url = profile_url
        self.max_retries = max_retries
        self.retry_wait_seconds = retry_wait_seconds
        logger.info(f"Facebook Profile Service initialized for URL: {profile_url}")

    def get_followers(self) -> Optional[int]:
        
        retries = 0

        while retries <= self.max_retries:
            # Create a fresh driver instance for each attempt
            driver = PlaywrightDriver()
            context = None
            
            try:
                # Initialize browser
                context = driver.initialize_driver()
                page = context.new_page()
                
                logger.info(f"Navigating to Facebook profile URL: {self.profile_url}")
                page.goto(self.profile_url, timeout=60000)
                time.sleep(5)  # Wait for the page to load completely
                
                content = page.content()
                
                # Regex pattern to find follower count
                # Try multiple patterns since Facebook uses different labels
                patterns = [
                    r'([\d,\.]+)\s+followers',
                    r'([\d,\.]+)\s+likes',
                    r'([\d,\.]+)\s+people like this',
                    r'"fan_count"[:\s]+([\d]+)',
                    r'"follower_count"[:\s]+([\d]+)',
                    r'"likers_count"[:\s]+([\d]+)',
                ]

                for pattern in patterns:
                    match = re.search(pattern, content, re.IGNORECASE)
                    if match:
                        followers_str = match.group(1).replace(',', '').replace('.', '')
                        followers_count = int(followers_str)
                        logger.info(f"Found count via pattern '{pattern}': {followers_count}")
                        return followers_count
                
                else:
                    logger.warning("Followers count not found on the page.")
                    retries += 1
                    time.sleep(self.retry_wait_seconds)
            
            except Exception as e:
                logger.error(f"Error while scraping Facebook profile: {e}")
                raise ScrapingError(f"Error while scraping Facebook profile: {e}")
            
            finally:
                if context:
                    driver.close(context=context)
        

if __name__ == "__main__":
    # Configure basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create service and get data
    service = FacebookProfileService()
    followers_count = service.get_followers()

    # Print results
    print(f"Facebook Followers Count: {followers_count if followers_count is not None else 'Not Found'}")