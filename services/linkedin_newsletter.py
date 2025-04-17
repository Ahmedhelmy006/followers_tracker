"""
LinkedIn Newsletter Service.

This module handles retrieving subscriber counts from LinkedIn newsletter pages
by extracting the data from the HTML response.
"""
import os, sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import re
import time
import logging
from typing import Dict, Any, Optional

from config.settings import LKD_NEWSLETTER
from utils.playwright_driver import PlaywrightDriver
from utils.exceptions import ScrapingError

logger = logging.getLogger(__name__)

class LinkedInNewsletterService:
    """
    Service for retrieving data from LinkedIn newsletter pages.
    
    This service extracts subscriber counts from LinkedIn newsletter pages
    by analyzing the HTML content of the page.
    """
    
    def __init__(self, newsletter_url: str = LKD_NEWSLETTER):
        """
        Initialize the LinkedIn Newsletter Service.
        
        Args:
            newsletter_url: URL of the LinkedIn newsletter to scrape.
                          If None, uses the default URL from settings.
        """
        self.newsletter_url = newsletter_url
        logger.info(f"LinkedIn Newsletter Service initialized for URL: {newsletter_url}")
    
    def get_subscribers(self) -> Optional[int]:
        """
        Get the number of subscribers for the LinkedIn newsletter.
        
        Returns:
            The number of subscribers as an integer, or None if not found
            
        Raises:
            ScrapingError: If there is an error during the scraping process
        """
        driver = PlaywrightDriver()
        
        try:
            # Initialize browser
            context = driver.initialize_driver()
            page = context.new_page()
            
            # Navigate to newsletter page
            logger.info(f"Navigating to LinkedIn newsletter: {self.newsletter_url}")
            page.goto(self.newsletter_url, timeout=120000)  # 2 minutes timeout
            
            # Wait for page to load
            logger.debug("Waiting for page content to load")
            time.sleep(3)  # Give JavaScript time to load
            
            # Extract page content
            page_content = page.content()
            
            # Extract subscriber count
            subscribers = self._extract_subscribers(page_content)
            
            if subscribers is not None:
                logger.info(f"Successfully extracted subscriber count: {subscribers}")
                return subscribers
            
            logger.warning("Could not find subscriber count on the page")
            return None
            
        except Exception as e:
            error_msg = f"Error scraping LinkedIn newsletter: {str(e)}"
            logger.error(error_msg)
            raise ScrapingError(error_msg)
        
        finally:
            # Clean up resources
            if 'context' in locals():
                driver.close(context)
                logger.debug("Browser context closed")
    
    def _extract_subscribers(self, page_content: str) -> Optional[int]:
        """
        Extract subscriber count from page content using regex.
        
        Args:
            page_content: HTML content of the LinkedIn newsletter page
            
        Returns:
            The number of subscribers as an integer, or None if not found
        """
        # Pattern to find "X followers" or "X subscribers" where X is a number (possibly with commas)
        patterns = [
            r'([\d,]+)\s+followers',  # Matches "441,469 followers"
            r'([\d,]+)\s+subscribers',  # Matches "X subscribers"
            r'subscribers&quot;:&quot;([\d,]+)&quot;',  # JSON format in HTML
            r'subscriberCount&quot;:&quot;([\d,]+)&quot;', # Alternative JSON format
            r'subscriberCount":"([\d,]+)"',  # Another JSON format
            r'followerCount":"([\d,]+)"',  # Another JSON format
        ]
        
        for pattern in patterns:
            match = re.search(pattern, page_content)
            if match:
                # Remove commas from the number and convert to int
                subscriber_text = match.group(1).replace(',', '')
                return int(subscriber_text)
        
        logger.debug("No regex patterns matched for subscriber count")
        return None
    
    def get_newsletter_data(self) -> Dict[str, Any]:
        """
        Get complete newsletter data including subscriber count.
        
        Returns:
            Dictionary containing newsletter data with subscriber count
        """
        subscribers = self.get_subscribers()
        
        # Extract newsletter name from the URL
        newsletter_name = "LinkedIn Newsletter"
        url_parts = self.newsletter_url.split('/')
        if len(url_parts) > 4:
            newsletter_name = url_parts[4].replace('-', ' ').title()
        
        return {
            "platform": "LinkedIn",
            "type": "Newsletter",
            "name": newsletter_name,
            "url": self.newsletter_url,
            "subscribers": subscribers if subscribers is not None else "Not Found",
            "timestamp": time.time()
        }


if __name__ == "__main__":
    # Configure basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create service and get data
    service = LinkedInNewsletterService()
    newsletter_data = service.get_newsletter_data()
    
    # Print results
    print(f"LinkedIn Newsletter Data: {newsletter_data}")