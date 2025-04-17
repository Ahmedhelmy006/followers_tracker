"""
LinkedIn Company Service.

This module handles retrieving follower counts from LinkedIn company pages.
It extracts data from the HTML response by looking for the followers count pattern.
"""

import re
import time
import logging
from typing import Dict, List, Optional, Any, Tuple
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.settings import (
    AIFC_LKD_PAGE,
    BI_LKD_PAGE,
    NBO_LKD_PAGE,
    EXCEL_CHEATSHEETS_LKD_PAGE
)
from utils.playwright_driver import PlaywrightDriver
from utils.exceptions import ScrapingError

logger = logging.getLogger(__name__)

class LinkedInCompanyService:
    """
    Service for retrieving data from LinkedIn company pages.
    
    This service extracts follower counts by analyzing the HTML content
    of LinkedIn company pages. It processes each company page with a fresh
    browser instance to avoid hitting login screens.
    """
    
    def __init__(self, company_urls: Optional[List[str]] = None):
        """
        Initialize the LinkedIn Company Service.
        
        Args:
            company_urls: List of LinkedIn company page URLs to scrape.
                          If None, uses the default list from settings.
        """
        # Use provided URLs or default to the ones from settings
        self.company_urls = company_urls or [
            AIFC_LKD_PAGE,
            BI_LKD_PAGE,
            NBO_LKD_PAGE,
            EXCEL_CHEATSHEETS_LKD_PAGE
        ]
        
        # Map URLs to company names for more readable output
        self.url_to_name_map = {
            AIFC_LKD_PAGE: "AI Finance Club",
            BI_LKD_PAGE: "Business Infographics",
            NBO_LKD_PAGE: "Nicolas Boucher Online",
            EXCEL_CHEATSHEETS_LKD_PAGE: "Excel Cheatsheets"
        }
        
        logger.info(f"LinkedIn Company Service initialized with {len(self.company_urls)} company pages")
    
    def get_company_followers(self, company_url: str) -> Optional[int]:
        """
        Get the number of followers for a specific LinkedIn company page.
        
        Args:
            company_url: URL of the LinkedIn company page
            
        Returns:
            The number of followers as an integer, or None if not found
            
        Raises:
            ScrapingError: If there is an error during the scraping process
        """
        # Create a new browser instance for each company page
        driver = PlaywrightDriver()
        
        try:
            # Initialize browser
            company_name = self.url_to_name_map.get(company_url, company_url)
            logger.info(f"Processing company page: {company_name} ({company_url})")
            
            context = driver.initialize_driver()
            page = context.new_page()
            
            # Navigate to company page
            logger.debug(f"Navigating to {company_url}")
            page.goto(company_url, timeout=120000)  # 2 minutes timeout
            
            # Wait for page to load
            logger.debug("Waiting for page content to load")
            time.sleep(3)  # Give JavaScript time to load
            
            # Extract page content
            page_content = page.content()
            
            # Extract followers count
            followers = self._extract_followers(page_content)
            
            if followers is not None:
                logger.info(f"Successfully extracted follower count for {company_name}: {followers}")
                return followers
            
            logger.warning(f"Could not find follower count for {company_name}")
            return None
            
        except Exception as e:
            error_msg = f"Error scraping LinkedIn company page {company_url}: {str(e)}"
            logger.error(error_msg)
            raise ScrapingError(error_msg)
        
        finally:
            # Clean up resources
            if 'context' in locals():
                driver.close(context)
                logger.debug("Browser context closed")
    
    def _extract_followers(self, page_content: str) -> Optional[int]:
        """
        Extract follower count from page content using regex.
        
        Args:
            page_content: HTML content of the LinkedIn company page
            
        Returns:
            The number of followers as an integer, or None if not found
        """
        # Pattern to find "X followers" where X is a number (possibly with commas)
        patterns = [
            r'(\d+,?\d*)\s+followers',  # Matches "631 followers" or "1,234 followers"
            r'followerCount&quot;:(\d+)',  # Matches followerCount JSON value
            r'followerCount":(\d+)',  # Alternative JSON format
            r'(\d+,?\d*)\s*follower',  # More general pattern
        ]
        
        for pattern in patterns:
            match = re.search(pattern, page_content)
            if match:
                # Remove commas from the number and convert to int
                follower_text = match.group(1).replace(',', '')
                return int(follower_text)
        
        logger.debug("No regex patterns matched for follower count")
        return None
    
    def get_all_company_data(self) -> List[Dict[str, Any]]:
        """
        Get follower data for all configured company pages.
        
        Returns:
            List of dictionaries containing company data with follower counts
            
        Note:
            Processes each company sequentially with a fresh browser instance
        """
        results = []
        
        for company_url in self.company_urls:
            try:
                company_name = self.url_to_name_map.get(company_url, company_url)
                followers = self.get_company_followers(company_url)
                
                company_data = {
                    "platform": "LinkedIn",
                    "type": "Company Page",
                    "name": company_name,
                    "url": company_url,
                    "followers": followers if followers is not None else "Not Found",
                    "timestamp": time.time()
                }
                
                results.append(company_data)
                
                # Small delay between companies to avoid rate limiting
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error processing company {company_url}: {str(e)}")
                # Add failed result with error information
                results.append({
                    "platform": "LinkedIn",
                    "type": "Company Page",
                    "name": self.url_to_name_map.get(company_url, company_url),
                    "url": company_url,
                    "followers": "Not Found",
                    "error": str(e),
                    "timestamp": time.time()
                })
        
        return results


if __name__ == "__main__":
    # Configure basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create service and get data
    service = LinkedInCompanyService()
    company_data = service.get_all_company_data()
    
    # Print results
    for company in company_data:
        print(f"{company['name']}: {company['followers']} followers")