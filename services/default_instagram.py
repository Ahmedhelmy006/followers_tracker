"""
Instagram Service - Fixed for zstd compression handling

This version properly handles zstd compressed responses from the API.
"""
import os, sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import json
import time
import logging
import requests
from typing import Dict, Any, Optional

# Try to import zstd decompression
try:
    import zstandard as zstd
    ZSTD_AVAILABLE = True
except ImportError:
    ZSTD_AVAILABLE = False
    logging.warning("zstandard package not available. Installing it may help with API responses.")

from config.settings import (
    INSTAGRAM_USERNAME,
    INSTAGRAM_API_ENDPOINT,
    INSTAGRAM_MAX_RETRIES
)
from utils.playwright_stealth_driver import PlaywrightStealthDriver
from utils.exceptions import APIError, ScrapingError

logger = logging.getLogger(__name__)

class InstagramService:
    """
    Service for retrieving data from Instagram with proper compression handling.
    """
    
    def __init__(self, username: str = INSTAGRAM_USERNAME):
        """
        Initialize the Instagram Service.
        
        Args:
            username: Instagram username to fetch data for
        """
        self.username = username
        self.max_retries = INSTAGRAM_MAX_RETRIES
        
        # Correct API endpoint based on your working example
        self.api_endpoint = "https://api.digitalbyte.cc/instagram/tucktools2.com"
        
        # Updated headers that work (from your successful request)
        self.api_headers = {
            "authority": "api.digitalbyte.cc",
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br",  # Removed zstd to avoid compression
            "accept-language": "en-US,en;q=0.9",
            "origin": "https://www.tucktools.com",
            "priority": "u=1, i",
            "referer": "https://www.tucktools.com/",
            "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Linux"',  # Changed to Linux for VM
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
        }
        
        logger.info(f"Instagram Service initialized for username: {username}")
        if not ZSTD_AVAILABLE:
            logger.info("Note: zstandard not available. Requesting uncompressed responses.")
    
    def _decompress_response(self, response: requests.Response) -> str:
        """
        Decompress response content if it's compressed.
        
        Args:
            response: requests Response object
            
        Returns:
            Decompressed text content
        """
        content_encoding = response.headers.get('content-encoding', '').lower()
        
        if content_encoding == 'zstd':
            if ZSTD_AVAILABLE:
                try:
                    # Decompress zstd content
                    dctx = zstd.ZstdDecompressor()
                    decompressed = dctx.decompress(response.content)
                    return decompressed.decode('utf-8')
                except Exception as e:
                    logger.error(f"Failed to decompress zstd content: {str(e)}")
                    raise ValueError(f"zstd decompression failed: {str(e)}")
            else:
                raise ValueError("Response is zstd compressed but zstandard package not available")
        
        # For other encodings (gzip, deflate, br), requests handles automatically
        return response.text
    
    def _get_followers_from_api(self) -> Dict[str, Any]:
        """
        Get follower count from the third-party API with proper compression handling.
        
        Returns:
            Dictionary with follower data or error information
        """
        try:
            # Use the correct API URL format
            api_url = f"{self.api_endpoint}/{self.username}"
            logger.info(f"Fetching Instagram data from API: {api_url}")
            
            # Create session to handle compression properly
            session = requests.Session()
            
            # Make request
            response = session.get(
                api_url,
                headers=self.api_headers,
                timeout=30
            )
            
            # Log response details for debugging
            logger.debug(f"API Response status: {response.status_code}")
            logger.debug(f"Content-Encoding: {response.headers.get('content-encoding', 'none')}")
            logger.debug(f"Content-Type: {response.headers.get('content-type', 'none')}")
            logger.debug(f"Content-Length: {len(response.content)}")
            
            if response.status_code != 200:
                error_msg = f"Instagram API returned error: {response.status_code}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg
                }
            
            # Handle compressed content
            try:
                text_content = self._decompress_response(response)
                logger.debug(f"Decompressed content preview: {text_content[:200]}...")
            except ValueError as e:
                logger.error(f"Decompression failed: {str(e)}")
                return {
                    "success": False,
                    "error": f"Failed to decompress response: {str(e)}"
                }
            
            if not text_content.strip():
                logger.error("API returned empty content after decompression")
                return {
                    "success": False,
                    "error": "Empty response from API"
                }
            
            # Parse JSON
            try:
                data = json.loads(text_content)
                
                # Extract follower count - adjust this based on actual API response structure
                # You may need to check the actual JSON structure
                followers_count = None
                
                # Try different possible keys
                possible_keys = [
                    "user_followers", 
                    "followers", 
                    "follower_count",
                    "data.user.edge_followed_by.count",
                    "graphql.user.edge_followed_by.count"
                ]
                
                for key in possible_keys:
                    if "." in key:
                        # Handle nested keys
                        keys = key.split(".")
                        temp_data = data
                        try:
                            for k in keys:
                                temp_data = temp_data[k]
                            if temp_data is not None:
                                followers_count = temp_data
                                break
                        except (KeyError, TypeError):
                            continue
                    else:
                        # Handle simple keys
                        if key in data and data[key] is not None:
                            followers_count = data[key]
                            break
                
                logger.debug(f"Full API response: {json.dumps(data, indent=2)}")
                
                if followers_count is not None and str(followers_count).replace(',', '').isdigit():
                    followers_count = int(str(followers_count).replace(',', ''))
                    logger.info(f"Successfully fetched follower count from API: {followers_count}")
                    return {
                        "success": True,
                        "followers": followers_count
                    }
                else:
                    logger.warning(f"API returned invalid follower count: {followers_count}")
                    logger.warning(f"Available keys in response: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                    return {
                        "success": False,
                        "error": f"Invalid follower count from API: {followers_count}"
                    }
                    
            except json.JSONDecodeError as e:
                error_msg = f"Failed to parse API response as JSON: {str(e)} - Content: {text_content[:200]}"
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
        Get follower count by scraping Instagram directly with Playwright Stealth.
        
        Returns:
            Dictionary with follower data or error information
        """
        driver = PlaywrightStealthDriver()
        follower_count = None
        
        try:
            logger.info(f"Attempting to scrape Instagram for username: {self.username}")
            
            # Initialize browser with stealth mode
            context = driver.initialize_driver(stealth_mode=True)
            page = context.new_page()
            
            # Enhanced VM compatibility scripts
            page.add_init_script("""
            () => {
                // Enhanced stealth for VMs
                Object.defineProperty(navigator, 'platform', {
                    get: () => 'Linux x86_64'
                });
                
                Object.defineProperty(navigator, 'hardwareConcurrency', {
                    get: () => 4
                });
                
                Object.defineProperty(navigator, 'deviceMemory', {
                    get: () => 8
                });
                
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // Remove automation traces
                delete navigator.__proto__.webdriver;
                
                // Mock realistic viewport
                Object.defineProperty(screen, 'width', { get: () => 1920 });
                Object.defineProperty(screen, 'height', { get: () => 1080 });
            }
            """)
            
            # Set up GraphQL response monitoring
            graphql_data = {"follower_count": None}
            
            def handle_response(response):
                try:
                    if "graphql" in response.url and response.status == 200:
                        logger.debug(f"GraphQL response detected: {response.url}")
                        response_json = response.json()
                        
                        # Search for follower count in the response
                        def find_follower_count(obj, path=""):
                            if isinstance(obj, dict):
                                for key, value in obj.items():
                                    current_path = f"{path}.{key}" if path else key
                                    if key in ["follower_count", "edge_followed_by"] and isinstance(value, (int, dict)):
                                        if isinstance(value, int):
                                            graphql_data["follower_count"] = value
                                            logger.info(f"Found follower count at {current_path}: {value}")
                                            return value
                                        elif isinstance(value, dict) and "count" in value:
                                            count = value["count"]
                                            graphql_data["follower_count"] = count
                                            logger.info(f"Found follower count at {current_path}.count: {count}")
                                            return count
                                    elif isinstance(value, (dict, list)):
                                        result = find_follower_count(value, current_path)
                                        if result is not None:
                                            return result
                            elif isinstance(obj, list):
                                for i, item in enumerate(obj):
                                    result = find_follower_count(item, f"{path}[{i}]")
                                    if result is not None:
                                        return result
                            return None
                        
                        find_follower_count(response_json)
                        
                except Exception as e:
                    logger.debug(f"Failed to parse GraphQL response: {str(e)}")
            
            page.on("response", handle_response)
            
            # Navigate to Instagram profile
            instagram_url = f"https://www.instagram.com/{self.username}/"
            logger.info(f"Navigating to Instagram profile: {instagram_url}")
            
            try:
                page.goto(instagram_url, timeout=90000, wait_until="domcontentloaded")
            except Exception as e:
                logger.warning(f"Navigation error: {str(e)}, continuing...")
            
            # Wait for content to load
            logger.info("Waiting for page to load and GraphQL requests to complete")
            
            try:
                page.wait_for_load_state("networkidle", timeout=20000)
            except Exception as e:
                logger.debug(f"Network idle timeout: {str(e)}")
            
            # Additional wait for VM environment
            time.sleep(10)
            
            # Check GraphQL results
            if graphql_data["follower_count"] is not None:
                follower_count = graphql_data["follower_count"]
                logger.info(f"Successfully extracted follower count from GraphQL: {follower_count}")
            else:
                # Fallback to page content parsing
                logger.debug("Attempting to extract follower count from page content")
                page_content = page.content()
                
                # Check for login redirect
                try:
                    page_title = page.title()
                    current_url = page.url
                    logger.debug(f"Page title: {page_title}")
                    logger.debug(f"Current URL: {current_url}")
                    
                    if "login" in current_url or "login" in page_title.lower():
                        logger.warning("Redirected to login page - scraping blocked")
                        return {
                            "success": False,
                            "error": "Redirected to login page - Instagram blocking detected"
                        }
                except Exception as e:
                    logger.debug(f"Could not check page details: {str(e)}")
                
                # Parse page content for follower count
                import re
                patterns = [
                    r'"follower_count":(\d+)',
                    r'"edge_followed_by":{"count":(\d+)}',
                    r'([\d,]+)\s+followers',
                    r'Followers</span><span[^>]*>([^<]+)',
                ]
                
                for i, pattern in enumerate(patterns):
                    try:
                        matches = re.findall(pattern, page_content, re.IGNORECASE)
                        if matches:
                            for match in matches:
                                follower_text = str(match).replace(',', '').strip()
                                if follower_text.isdigit():
                                    follower_count = int(follower_text)
                                    logger.info(f"Extracted follower count using pattern {i+1}: {follower_count}")
                                    break
                            if follower_count:
                                break
                    except Exception as e:
                        logger.debug(f"Pattern {i+1} failed: {str(e)}")
            
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
            if 'context' in locals():
                try:
                    driver.close(context)
                    logger.debug("Browser context closed")
                except Exception as e:
                    logger.debug(f"Error closing browser context: {str(e)}")
    
    def get_followers(self) -> Dict[str, Any]:
        """
        Get the number of followers for the Instagram account.
        
        Returns:
            Dictionary containing follower data
        """
        # Try API first
        api_result = self._get_followers_from_api()
        
        if api_result["success"]:
            return {
                "platform": "Instagram",
                "username": self.username,
                "followers": api_result["followers"],
                "timestamp": time.time(),
                "source": "api"
            }
        
        logger.warning(f"API failed: {api_result['error']}")
        
        # Fallback to scraping
        scrape_result = self._get_followers_from_scraping()
        
        if scrape_result["success"]:
            return {
                "platform": "Instagram",
                "username": self.username,
                "followers": scrape_result["followers"],
                "timestamp": time.time(),
                "source": "scraping"
            }
        
        # Both methods failed
        logger.error("Both API and scraping methods failed")
        return {
            "platform": "Instagram",
            "username": self.username,
            "followers": "Not Found",
            "timestamp": time.time(),
            "error": f"API: {api_result['error']}, Scraping: {scrape_result['error']}"
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
        level=logging.DEBUG,  # Use DEBUG for more detailed logs
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create service and get data
    service = InstagramService()
    account_data = service.get_account_data()
    
    # Print results
    print(f"Instagram Data: {account_data}")
