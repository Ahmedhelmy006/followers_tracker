"""
Instagram Service.

This module handles retrieving follower counts from Instagram using a third-party API
with a fallback to direct scraping using Playwright if the API fails.
"""
import os, sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import json
import time
import logging
import requests
import math
from typing import Dict, Any, Optional, Tuple, Union

from config.settings import (
    INSTAGRAM_USERNAME,
    INSTAGRAM_API_ENDPOINT,
    INSTAGRAM_MAX_RETRIES
)
from utils.playwright_driver import PlaywrightDriver
from utils.exceptions import APIError, ScrapingError

logger = logging.getLogger(__name__)

class InstagramService:
    """
    Service for retrieving data from Instagram.
    
    This service fetches follower metrics for Instagram accounts using a third-party API
    with a fallback to direct scraping if the API fails.
    """
    
    def __init__(self, username: str = INSTAGRAM_USERNAME):
        """
        Initialize the Instagram Service.
        
        Args:
            username: Instagram username to fetch data for
        """
        self.username = username
        self.api_endpoint = INSTAGRAM_API_ENDPOINT
        self.max_retries = INSTAGRAM_MAX_RETRIES
        
        # Headers for the third-party API request
        self.api_headers = {
            "authority": "fanhub.pro",
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-GB,en;q=0.9,de-DE;q=0.8,de;q=0.7,ar-AE;q=0.6,ar;q=0.5,en-US;q=0.4",
            "dnt": "1",
            "origin": "https://www.tucktools.com",
            "priority": "u=1, i",
            "referer": "https://www.tucktools.com/",
            "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "sec-gpc": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
        }
        
        logger.info(f"Instagram Service initialized for username: {username}")
    
    def _get_followers_from_api(self) -> Dict[str, Any]:
        """
        Get follower count from the third-party API.
        
        Returns:
            Dictionary with follower data or error information
        """
        params = {"username": self.username}
        
        try:
            logger.info(f"Fetching Instagram data from API for username: {self.username}")
            response = requests.get(
                self.api_endpoint,
                headers=self.api_headers,
                params=params,
                timeout=30
            )
            
            if response.status_code != 200:
                error_msg = f"Instagram API returned error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg
                }
            
            try:
                data = json.loads(response.text)
                followers_count = data.get("user_followers")
                
                if followers_count and followers_count != "Not Found":
                    logger.info(f"Successfully fetched follower count from API: {followers_count}")
                    return {
                        "success": True,
                        "followers": int(followers_count) if str(followers_count).isdigit() else followers_count
                    }
                else:
                    logger.warning("API returned invalid follower count")
                    return {
                        "success": False,
                        "error": "Invalid follower count from API"
                    }
            except (json.JSONDecodeError, ValueError) as e:
                error_msg = f"Failed to parse API response: {str(e)}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg
                }
                
        except requests.RequestException as e:
            error_msg = f"Request error when fetching from API: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }
            
        except Exception as e:
            error_msg = f"Unexpected error when fetching from API: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }
    
    def _get_followers_from_scraping(self) -> Dict[str, Any]:
        """
        Get follower count by scraping Instagram directly with Playwright.
        
        Returns:
            Dictionary with follower data or error information
        """
        driver = PlaywrightDriver()
        follower_count = None
        
        try:
            logger.info(f"Attempting to scrape Instagram for username: {self.username}")
            
            # Initialize browser
            context = driver.initialize_driver()
            page = context.new_page()
            
            # Set up request interception for graphql queries
            graphql_data = {"follower_count": None}
            
            def handle_response(response):
                if "graphql/query" in response.url and response.status == 200:
                    try:
                        response_json = response.json()
                        if "data" in response_json and "user" in response_json["data"]:
                            user_data = response_json["data"]["user"]
                            if "follower_count" in user_data:
                                graphql_data["follower_count"] = user_data["follower_count"]
                                logger.info(f"Found follower count in GraphQL response: {graphql_data['follower_count']}")
                    except Exception as e:
                        logger.debug(f"Failed to parse GraphQL response: {str(e)}")
            
            page.on("response", handle_response)
            
            # Go to Instagram profile page
            instagram_url = f"https://www.instagram.com/{self.username}/"
            logger.debug(f"Navigating to Instagram profile: {instagram_url}")
            
            page.goto(instagram_url, timeout=60000)  # 1 minute timeout
            
            # Wait for potential GraphQL responses
            logger.debug("Waiting for page to load and GraphQL requests to complete")
            page.wait_for_load_state("networkidle", timeout=30000)
            time.sleep(5)  # Additional wait for any delayed responses
            
            # Check if we got the follower count from GraphQL
            if graphql_data["follower_count"] is not None:
                follower_count = graphql_data["follower_count"]
            else:
                # Fallback: Try to extract from page content
                logger.debug("Attempting to extract follower count from page content")
                page_content = page.content()
                
                # Different patterns to find follower count in page content
                import re
                patterns = [
                    r'"follower_count":(\d+)',
                    r'"edge_followed_by":{"count":(\d+)}',
                    r'([\d,]+) followers',
                    r'Followers</span><span class="[^"]*">([^<]+)'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, page_content)
                    if match:
                        follower_text = match.group(1).replace(',', '')
                        if follower_text.isdigit():
                            follower_count = int(follower_text)
                            logger.info(f"Extracted follower count from page: {follower_count}")
                            break
            
            if follower_count is not None:
                return {
                    "success": True,
                    "followers": follower_count
                }
            else:
                logger.warning("Could not extract follower count from Instagram")
                return {
                    "success": False,
                    "error": "Could not find follower count on Instagram"
                }
                
        except Exception as e:
            error_msg = f"Error scraping Instagram: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }
            
        finally:
            # Clean up resources
            if 'context' in locals():
                driver.close(context)
                logger.debug("Browser context closed")
    
    def get_followers(self) -> Dict[str, Any]:
        """
        Get the number of followers for the Instagram account.
        
        Uses a third-party API first, with fallback to direct scraping and
        exponential backoff for retries.
        
        Returns:
            Dictionary containing follower data
        """
        # First, try the third-party API
        api_result = self._get_followers_from_api()
        
        if api_result["success"]:
            return {
                "platform": "Instagram",
                "username": self.username,
                "followers": api_result["followers"],
                "timestamp": time.time(),
                "source": "third-party-api"
            }
        
        # If API failed, implement exponential backoff with scraping attempts
        retry_count = 0
        base_wait_time = 120  # 2 minutes in seconds
        
        while retry_count < self.max_retries:
            # Calculate wait time with exponential backoff
            wait_time = base_wait_time * (2 ** retry_count)
            logger.info(f"API attempt failed. Retry {retry_count + 1}/{self.max_retries} after {wait_time/60:.1f} minutes")
            
            # Try scraping during the wait time
            scrape_result = self._get_followers_from_scraping()
            
            if scrape_result["success"]:
                logger.info(f"Successfully retrieved follower count via scraping: {scrape_result['followers']}")
                return {
                    "platform": "Instagram",
                    "username": self.username,
                    "followers": scrape_result["followers"],
                    "timestamp": time.time(),
                    "source": "direct-scraping"
                }
            
            # If scraping also failed, wait and then retry the API
            logger.info(f"Scraping attempt failed. Waiting {wait_time/60:.1f} minutes before retrying API...")
            time.sleep(wait_time)
            
            # Retry the API
            api_result = self._get_followers_from_api()
            
            if api_result["success"]:
                logger.info(f"Successfully retrieved follower count via API retry: {api_result['followers']}")
                return {
                    "platform": "Instagram",
                    "username": self.username,
                    "followers": api_result["followers"],
                    "timestamp": time.time(),
                    "source": "third-party-api-retry"
                }
            
            retry_count += 1
        
        # If all retries failed, return not found
        logger.error(f"All attempts to retrieve Instagram follower count failed after {self.max_retries} retries")
        return {
            "platform": "Instagram",
            "username": self.username,
            "followers": "Not Found",
            "timestamp": time.time(),
            "error": "All retrieval attempts failed"
        }
    
    def get_account_data(self) -> Dict[str, Any]:
        """
        Get complete Instagram account data including follower count.
        
        Returns:
            Dictionary containing account data with follower count
        """
        return self.get_followers()


if __name__ == "__main__":
    # Configure basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create service and get data
    service = InstagramService()
    account_data = service.get_account_data()
    
    # Print results
    print(f"Instagram Data: {account_data}")