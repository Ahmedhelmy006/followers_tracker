"""
LinkedIn Profile Service.

This module handles retrieving follower counts from LinkedIn personal profiles.
It uses regex pattern matching to extract data from the public HTML response.
"""

import re
import time
import logging
from typing import Optional, Dict, Any
import os, sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from config.settings import NICOLAS_LKD_PROFILE
from utils.playwright_driver import PlaywrightDriver
from utils.exceptions import ScrapingError

logger = logging.getLogger(__name__)

class LinkedInProfileService:
    """
    Service for retrieving data from LinkedIn personal profiles.
    
    This service extracts follower counts using regex pattern matching
    from the HTML of LinkedIn profile pages.
    """
    
    def __init__(self, profile_url: str = NICOLAS_LKD_PROFILE, max_retries: int = 5, retry_wait_seconds: int = 10):
        """
        Initialize the LinkedIn Profile Service.
        
        Args:
            profile_url: URL of the LinkedIn profile to scrape, defaults to configured URL
            max_retries: Maximum number of retry attempts if follower count is not found
            retry_wait_seconds: Wait time in seconds between retry attempts
        """
        self.profile_url = profile_url
        self.max_retries = max_retries
        self.retry_wait_seconds = retry_wait_seconds
        logger.info(f"LinkedIn Profile Service initialized for URL: {profile_url}")
    
    def get_followers(self) -> Optional[int]:
        """
        Get the number of followers for the LinkedIn profile.
        
        Returns:
            The number of followers as an integer, or None if not found.
            
        Raises:
            ScrapingError: If there is an error during the scraping process.
        """
        driver = PlaywrightDriver()
        retries = 0
        
        while retries <= self.max_retries:
            try:
                # Initialize browser
                context = driver.initialize_driver()
                page = context.new_page()
                
                # Navigate to profile page
                logger.info(f"Navigating to LinkedIn profile: {self.profile_url} (Attempt {retries + 1}/{self.max_retries + 1})")
                page.goto(self.profile_url, timeout=120000)  # 2 minutes timeout
                
                # Wait for page to load
                logger.debug("Waiting for page content to load")
                time.sleep(3)  # Give JavaScript time to load
                
                # Extract page content
                page_content = page.content()
                
                # Extract followers count
                followers = self._extract_followers(page_content)
                
                if followers is not None:
                    logger.info(f"Successfully extracted follower count: {followers}")
                    return followers
                
                # Close the context before retrying
                driver.close(context)
                
                # If we reach the max retries, return None
                if retries == self.max_retries:
                    logger.warning(f"Could not find follower count after {retries + 1} attempts")
                    return None
                
                # Increment retry counter and wait before next attempt
                retries += 1
                wait_time = self.retry_wait_seconds
                logger.info(f"Follower count not found. Retrying in {wait_time} seconds (Attempt {retries + 1}/{self.max_retries + 1})")
                time.sleep(wait_time)
                
                # Create a new driver for the next attempt
                driver = PlaywrightDriver()
                
            except Exception as e:
                error_msg = f"Error scraping LinkedIn profile: {str(e)}"
                logger.error(error_msg)
                
                # Clean up resources
                if 'context' in locals():
                    driver.close(context)
                
                # If we reach the max retries, raise the error
                if retries == self.max_retries:
                    raise ScrapingError(error_msg)
                
                # Increment retry counter and wait before next attempt
                retries += 1
                wait_time = self.retry_wait_seconds
                logger.info(f"Error occurred. Retrying in {wait_time} seconds (Attempt {retries + 1}/{self.max_retries + 1})")
                time.sleep(wait_time)
                
                # Create a new driver for the next attempt
                driver = PlaywrightDriver()
        
        # This point should never be reached due to the return and raise statements above
        return None
    
    def _extract_followers(self, page_content: str) -> Optional[int]:
        """
        Extract follower count from page content using regex.
        
        Args:
            page_content: HTML content of the LinkedIn profile page
            
        Returns:
            The number of followers as an integer, or None if not found
        """
        # Primary pattern for follower count
        primary_match = re.search(r'"name":"Follows","userInteractionCount":(\d+)', page_content)
        if primary_match:
            return int(primary_match.group(1))
        
        # Fallback pattern
        fallback_match = re.search(r'followerCount":(\d+)', page_content)
        if fallback_match:
            return int(fallback_match.group(1))
        
        # Second fallback for older LinkedIn format
        text_match = re.search(r'(\d+,?\d*) followers', page_content)
        if text_match:
            follower_text = text_match.group(1).replace(',', '')
            return int(follower_text)
            
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
    
    # Create service and get data
    service = LinkedInProfileService()
    profile_data = service.get_profile_data()
    
    # Print results
    print(f"LinkedIn Profile Data: {profile_data}")