"""
Twitter (X) Service.

This module handles retrieving follower counts from Twitter (X) using the Twitter API.
"""
import os, sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
import logging
import requests
from typing import Dict, Any, Optional

from config.settings import TWITTER_USERNAME, TWITTER_API_ENDPOINT, TWITTER_BEARER_TOKEN
from utils.exceptions import APIError, RateLimitError



logger = logging.getLogger(__name__)

class TwitterService:
    """
    Service for retrieving data from Twitter (X) API.
    
    This service fetches follower metrics for Twitter accounts using the Twitter API.
    """
    
    def __init__(self, username: str = TWITTER_USERNAME, bearer_token: Optional[str] = None):
        """
        Initialize the Twitter Service.
        
        Args:
            username: Twitter username to fetch data for
            bearer_token: Twitter API bearer token for authentication.
                         If None, uses the token from environment variables.
        """
        self.username = username
        self.bearer_token = bearer_token or TWITTER_BEARER_TOKEN
        
        if not self.bearer_token:
            logger.warning("No Twitter bearer token provided. API calls will likely fail.")
            
        logger.info(f"Twitter Service initialized for username: {username}")
    
    def get_followers(self, retry_on_failure=True) -> Dict[str, Any]:
            """
            Get the number of followers for the Twitter account.
            
            Args:
                retry_on_failure: If True, wait 15 minutes and retry once if the initial request fails
                
            Returns:
                Dictionary containing follower data
                
            Raises:
                APIError: If there is an error with the API request
                RateLimitError: If Twitter API rate limit is reached
            """
            url = f"https://api.twitter.com/2/users/by/username/{self.username}?user.fields=public_metrics"
            headers = {"Authorization": f"Bearer {self.bearer_token}"}
            
            try:
                logger.info(f"Fetching Twitter data for username: {self.username}")
                response = requests.get(url, headers=headers, timeout=30)
                
                # Check for rate limiting
                if response.status_code == 429:
                    reset_time = response.headers.get('x-rate-limit-reset', 'unknown')
                    error_msg = f"Twitter API rate limit exceeded. Reset at: {reset_time}"
                    logger.error(error_msg)
                    
                    if retry_on_failure:
                        logger.info("Rate limit hit. Waiting 15 minutes before retry...")
                        time.sleep(900)  # Wait 15 minutes (900 seconds)
                        logger.info("Retrying Twitter API request after waiting...")
                        return self.get_followers(retry_on_failure=False)  # Retry once
                    
                    raise RateLimitError(error_msg, status_code=429, response=response.text)
                
                # Check for other API errors
                if response.status_code != 200:
                    error_msg = f"Twitter API returned error: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    
                    if retry_on_failure:
                        logger.info("API error. Waiting 15 minutes before retry...")
                        time.sleep(900)  # Wait 15 minutes (900 seconds)
                        logger.info("Retrying Twitter API request after waiting...")
                        return self.get_followers(retry_on_failure=False)  # Retry once
                    
                    raise APIError(error_msg, status_code=response.status_code, response=response.text)
                
                data = response.json()
                
                # Extract follower count from response
                if "data" in data and "public_metrics" in data["data"]:
                    followers_count = data["data"]["public_metrics"].get("followers_count", 0)
                    logger.info(f"Successfully fetched follower count for {self.username}: {followers_count}")
                    
                    return {
                        "platform": "Twitter",
                        "username": self.username,
                        "followers": followers_count,
                        "timestamp": time.time(),
                        "raw_metrics": data["data"]["public_metrics"]
                    }
                else:
                    logger.warning(f"Could not find followers data in API response for {self.username}")
                    logger.debug(f"Response data: {data}")
                    
                    if retry_on_failure:
                        logger.info("No follower data in response. Waiting 15 minutes before retry...")
                        time.sleep(900)  # Wait 15 minutes (900 seconds)
                        logger.info("Retrying Twitter API request after waiting...")
                        return self.get_followers(retry_on_failure=False)  # Retry once
                    
                    return {
                        "platform": "Twitter",
                        "username": self.username,
                        "followers": "Not Found",
                        "timestamp": time.time(),
                        "error": "No follower data in response"
                    }
                    
            except (requests.RequestException, requests.Timeout) as e:
                error_msg = f"Network error when fetching Twitter data: {str(e)}"
                logger.error(error_msg)
                
                if retry_on_failure:
                    logger.info("Network error. Waiting 15 minutes before retry...")
                    time.sleep(900)  # Wait 15 minutes (900 seconds)
                    logger.info("Retrying Twitter API request after waiting...")
                    return self.get_followers(retry_on_failure=False)  # Retry once
                
                return {
                    "platform": "Twitter",
                    "username": self.username,
                    "followers": "Not Found",
                    "timestamp": time.time(),
                    "error": error_msg
                }
                
            except (APIError, RateLimitError) as e:
                # These errors should already have been handled with a retry if retry_on_failure was True
                # Re-raise them for the caller
                raise
                
            except Exception as e:
                error_msg = f"Unexpected error fetching Twitter data: {str(e)}"
                logger.error(error_msg)
                
                if retry_on_failure:
                    logger.info("Unexpected error. Waiting 15 minutes before retry...")
                    time.sleep(900)  # Wait 15 minutes (900 seconds)
                    logger.info("Retrying Twitter API request after waiting...")
                    return self.get_followers(retry_on_failure=False)  # Retry once
                
                return {
                    "platform": "Twitter",
                    "username": self.username,
                    "followers": "Not Found",
                    "timestamp": time.time(),
                    "error": error_msg
                }
    
    def get_account_data(self) -> Dict[str, Any]:
        """
        Get complete Twitter account data including follower count.
        
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
    service = TwitterService()
    account_data = service.get_account_data()
    
    # Print results
    print(f"Twitter Data: {account_data}")