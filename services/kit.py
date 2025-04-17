"""
Kit Service.

This module handles retrieving subscriber counts and other statistics
from the Kit (formerly ConvertKit) API.
"""

import time
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from config.settings import KIT_API_KEY, KIT_GROWTH_STATS_ENDPOINT
from utils.exceptions import APIError, RateLimitError

logger = logging.getLogger(__name__)

class KitService:
    """
    Service for retrieving data from the Kit API.
    
    This service fetches subscriber statistics, including daily, weekly, 
    and monthly data from the Kit API.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Kit Service.
        
        Args:
            api_key: Kit API key for authentication. If None, uses the key from settings.
        """
        self.api_key = api_key or KIT_API_KEY
        self.endpoint = KIT_GROWTH_STATS_ENDPOINT
        
        if not self.api_key:
            logger.warning("No Kit API key provided. API calls will likely fail.")
            
        logger.info("Kit Service initialized")
    
    def get_daily_subscribers(self) -> Dict[str, Any]:
        """
        Get the daily subscribers count from Kit.
        
        Returns:
            Dictionary containing subscriber data for the previous day
            
        Raises:
            APIError: If there is an error with the API request
        """
        return self._pull_stats(time_range="daily")
    
    def get_weekly_subscribers(self) -> Dict[str, Any]:
        """
        Get the weekly subscribers count from Kit.
        
        Returns:
            Dictionary containing subscriber data for the past 7 days
            
        Raises:
            APIError: If there is an error with the API request
        """
        return self._pull_stats(time_range="weekly")
    
    def get_monthly_subscribers(self) -> Dict[str, Any]:
        """
        Get the monthly subscribers count from Kit.
        
        Returns:
            Dictionary containing subscriber data for the past 30 days
            
        Raises:
            APIError: If there is an error with the API request
        """
        return self._pull_stats(time_range="monthly")
    
    def _pull_stats(self, time_range: str = "daily") -> Dict[str, Any]:
        """
        Pull statistics from Kit API for a specific time range.
        
        Args:
            time_range: Time range for the statistics. Options: "daily", "weekly", "monthly"
            
        Returns:
            Dictionary containing subscriber statistics
            
        Raises:
            APIError: If there is an error with the API request
        """
        try:
            headers = {
                'Accept': 'application/json',
                'X-Kit-Api-Key': self.api_key
            }
            
            today = datetime.now() + timedelta(hours=1)  # CET adjustment
            
            if time_range == "daily":
                start_date = today - timedelta(days=1)
                end_date = start_date
            elif time_range == "weekly":
                start_date = today - timedelta(days=7)
                end_date = today - timedelta(days=1)
            elif time_range == "monthly":
                start_date = today - timedelta(days=30)
                end_date = today - timedelta(days=1)
            else:
                error_msg = f"Invalid time range: {time_range}. Must be 'daily', 'weekly', or 'monthly'"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            starting_date = start_date.strftime("%Y-%m-%dT00:00:00+01:00")
            ending_date = end_date.strftime("%Y-%m-%dT23:59:59+01:00")
            
            params = {
                "starting": starting_date,
                "ending": ending_date
            }
            
            logger.info(f"Fetching Kit {time_range} stats from {starting_date} to {ending_date}")
            
            response = requests.get(
                self.endpoint,
                headers=headers,
                params=params,
                timeout=30
            )
            
            if response.status_code == 429:
                error_msg = "Kit API rate limit exceeded"
                logger.error(error_msg)
                raise RateLimitError(error_msg, status_code=429, response=response.text)
            
            if response.status_code != 200:
                error_msg = f"Kit API returned error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise APIError(error_msg, status_code=response.status_code, response=response.text)
            
            data = response.json()
            logger.debug(f"{time_range.capitalize()} data: {data}")
            
            # Extract the statistics from the response
            stats = data.get("stats", {})
            
            result = {
                "platform": "Kit",
                "time_range": time_range,
                "subscribers": stats.get("subscribers", 0),
                "cancellations": stats.get("cancellations", 0),
                "net_new_subscribers": stats.get("net_new_subscribers", 0),
                "new_subscribers": stats.get("new_subscribers", 0),
                "timestamp": time.time()
            }
            
            logger.info(f"Successfully fetched Kit {time_range} stats: {result['subscribers']} subscribers")
            return result
            
        except (APIError, RateLimitError):
            # Re-raise these specific errors
            raise
            
        except requests.RequestException as e:
            error_msg = f"Network error when fetching Kit data: {str(e)}"
            logger.error(error_msg)
            
            return {
                "platform": "Kit",
                "time_range": time_range,
                "subscribers": "Not Found",
                "cancellations": "Not Found",
                "net_new_subscribers": "Not Found",
                "new_subscribers": "Not Found",
                "timestamp": time.time(),
                "error": error_msg
            }
            
        except Exception as e:
            error_msg = f"Unexpected error fetching Kit data: {str(e)}"
            logger.error(error_msg)
            
            return {
                "platform": "Kit",
                "time_range": time_range,
                "subscribers": "Not Found",
                "cancellations": "Not Found",
                "net_new_subscribers": "Not Found",
                "new_subscribers": "Not Found",
                "timestamp": time.time(),
                "error": error_msg
            }
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all subscriber statistics (daily, weekly, monthly).
        
        Returns:
            Dictionary containing all subscriber statistics
        """
        try:
            daily_stats = self.get_daily_subscribers()
            weekly_stats = self.get_weekly_subscribers()
            monthly_stats = self.get_monthly_subscribers()
            
            return {
                "daily": daily_stats,
                "weekly": weekly_stats,
                "monthly": monthly_stats
            }
            
        except Exception as e:
            logger.error(f"Error fetching all Kit stats: {str(e)}")
            return {
                "daily": {"error": str(e), "subscribers": "Not Found"},
                "weekly": {"error": str(e), "subscribers": "Not Found"},
                "monthly": {"error": str(e), "subscribers": "Not Found"}
            }


if __name__ == "__main__":
    # Configure basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create service and get data
    service = KitService()
    
    # Get daily subscribers
    daily_data = service.get_daily_subscribers()
    print(f"Daily subscribers: {daily_data['subscribers']}")
    
    # Get all stats
    all_stats = service.get_all_stats()
    print(f"All Kit stats: {all_stats}")