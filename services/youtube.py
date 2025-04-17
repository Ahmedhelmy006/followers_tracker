"""
YouTube Service.

This module handles retrieving subscriber and view counts from YouTube
using the YouTube Data API.
"""
import os, sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import time
import logging
import requests
import json
import os
from typing import Dict, Any, Optional

from config.settings import YOUTUBE_STATS_ENDPOINT, YT_API_KEY, YT_CHANNEL_ID
from utils.exceptions import APIError, RateLimitError

logger = logging.getLogger(__name__)

class YouTubeService:
    """
    Service for retrieving data from YouTube.
    
    This service fetches subscriber and view counts from the YouTube Data API.
    """
    
    def __init__(self, api_key: Optional[str] = None, channel_id: Optional[str] = None):
        """
        Initialize the YouTube Service.
        
        Args:
            api_key: YouTube API key for authentication. If None, uses the key from settings.
            channel_id: YouTube channel ID. If None, uses the ID from settings.
        """
        self.api_key = api_key or YT_API_KEY
        self.channel_id = channel_id or YT_CHANNEL_ID
        
        # Build the endpoint URL
        if self.api_key and self.channel_id:
            self.endpoint = f'https://www.googleapis.com/youtube/v3/channels?part=statistics&id={self.channel_id}&key={self.api_key}'
        else:
            self.endpoint = YOUTUBE_STATS_ENDPOINT
        
        if not self.api_key:
            logger.warning("No YouTube API key provided. API calls will likely fail.")
            
        if not self.channel_id:
            logger.warning("No YouTube channel ID provided. API calls will likely fail.")
            
        logger.info(f"YouTube Service initialized for channel ID: {self.channel_id}")
    
    def get_channel_stats(self, max_retries: int = 3) -> Dict[str, Any]:
        """
        Get channel statistics including subscriber and view counts.
        
        Args:
            max_retries: Maximum number of retry attempts
            
        Returns:
            Dictionary containing channel statistics
            
        Raises:
            APIError: If there is an error with the API request
        """
        retries = 0
        
        while retries <= max_retries:
            try:
                logger.info(f"Fetching YouTube channel statistics (attempt {retries + 1}/{max_retries + 1})")
                
                response = requests.get(self.endpoint, timeout=30)
                
                # Check for rate limiting
                if response.status_code == 403 and "quotaExceeded" in response.text:
                    error_msg = "YouTube API quota exceeded"
                    logger.error(error_msg)
                    
                    if retries == max_retries:
                        raise RateLimitError(error_msg, status_code=403, response=response.text)
                        
                    retries += 1
                    # Wait before retrying (exponential backoff)
                    time.sleep(2 ** retries)
                    continue
                
                # Check for other API errors
                if response.status_code != 200:
                    error_msg = f"YouTube API returned error: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    
                    if retries == max_retries:
                        raise APIError(error_msg, status_code=response.status_code, response=response.text)
                        
                    retries += 1
                    # Wait before retrying (exponential backoff)
                    time.sleep(2 ** retries)
                    continue
                
                # Parse the JSON response
                data = response.json()
                
                # Extract statistics
                if "items" in data and len(data["items"]) > 0:
                    stats = data["items"][0]["statistics"]
                    
                    subscriber_count = int(stats.get("subscriberCount", 0))
                    view_count = int(stats.get("viewCount", 0))
                    
                    logger.info(f"Successfully fetched YouTube stats: {subscriber_count} subscribers, {view_count} views")
                    
                    # Save to local file for backup/debugging
                    self._save_stats_to_file(subscriber_count, view_count)
                    
                    return {
                        "platform": "YouTube",
                        "channel_id": self.channel_id,
                        "subscribers": subscriber_count,
                        "views": view_count,
                        "timestamp": time.time()
                    }
                else:
                    error_msg = "YouTube API response did not contain channel statistics"
                    logger.error(error_msg)
                    logger.debug(f"Response data: {data}")
                    
                    if retries == max_retries:
                        return {
                            "platform": "YouTube",
                            "channel_id": self.channel_id,
                            "subscribers": "Not Found",
                            "views": "Not Found",
                            "timestamp": time.time(),
                            "error": error_msg
                        }
                        
                    retries += 1
                    # Wait before retrying (exponential backoff)
                    time.sleep(2 ** retries)
                
            except (requests.RequestException, requests.Timeout) as e:
                error_msg = f"Network error when fetching YouTube data: {str(e)}"
                logger.error(error_msg)
                
                if retries == max_retries:
                    return {
                        "platform": "YouTube",
                        "channel_id": self.channel_id,
                        "subscribers": "Not Found",
                        "views": "Not Found",
                        "timestamp": time.time(),
                        "error": error_msg
                    }
                    
                retries += 1
                # Wait before retrying (exponential backoff)
                time.sleep(2 ** retries)
                
            except Exception as e:
                error_msg = f"Unexpected error fetching YouTube data: {str(e)}"
                logger.error(error_msg)
                
                if retries == max_retries:
                    return {
                        "platform": "YouTube",
                        "channel_id": self.channel_id,
                        "subscribers": "Not Found",
                        "views": "Not Found",
                        "timestamp": time.time(),
                        "error": error_msg
                    }
                    
                retries += 1
                # Wait before retrying (exponential backoff)
                time.sleep(2 ** retries)
        
        # This should never be reached due to the return statements above
        return {
            "platform": "YouTube",
            "channel_id": self.channel_id,
            "subscribers": "Not Found",
            "views": "Not Found",
            "timestamp": time.time(),
            "error": "Maximum retries reached"
        }
    
    def _save_stats_to_file(self, subscribers: int, views: int) -> None:
        """
        Save statistics to a local file for backup/debugging.
        
        Args:
            subscribers: Number of subscribers
            views: Number of views
        """
        try:
            with open("data/youtube_stats.txt", "w") as file:
                file.write(f"{subscribers}\n")
                file.write(f"{views}\n")
                file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                
            logger.debug("Saved YouTube stats to file")
        except Exception as e:
            logger.warning(f"Failed to save YouTube stats to file: {str(e)}")


if __name__ == "__main__":
    # Configure basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create service and get data
    service = YouTubeService()
    stats = service.get_channel_stats()
    
    # Print results
    print(f"YouTube Stats: {stats}")