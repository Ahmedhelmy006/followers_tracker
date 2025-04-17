from playwright.sync_api import sync_playwright, BrowserContext
import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class PlaywrightDriver:
    """
    A utility class to manage Playwright browser automation.
    
    This class handles browser initialization, cookie management, and cleanup.
    """
    
    def __init__(self, cookies_file: Optional[str] = None):
        """
        Initialize the PlaywrightDriver.
        
        Args:
            cookies_file: Path to a JSON file containing cookies for authentication.
        """
        self.cookies_file = cookies_file
        self.playwright = None
        self.browser = None
        

    def initialize_driver(self, user_agent_type: str = "default") -> BrowserContext:
        """
        Start the browser and initialize a new context.
        
        Args:
            user_agent_type: Type of user agent to use ("default", "random", or "mobile")
            
        Returns:
            A browser context object that can be used to create pages.
            
        Raises:
            Exception: If browser initialization fails.
        """
        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(
                headless=False,
                args=[
                    '--disable-blink-features=AutomationControlled',  # Disable the AutomationControlled flag
                    '--no-sandbox',                                   # Useful for some environments
                    '--disable-infobars',                             # Removes "Chrome is being controlled by automated software"
                    '--disable-dev-shm-usage',                        # Prevents shared memory issues
                    '--disable-extensions',                           # Disables all extensions
                    '--disable-gpu',                                  # Disables GPU hardware acceleration
                ]
            )
            
            # Select a user agent based on the specified type
            user_agent = self._get_user_agent(user_agent_type)
            
            # Create context with user agent
            context = self.browser.new_context(
                user_agent=user_agent,
                viewport={'width': 1920, 'height': 1080},  # Default viewport
                locale="en-US"
            )
            
            # Additional context settings
            context.set_default_timeout(60000)  # 60 seconds default timeout
            
            # Add cookies if provided
            if self.cookies_file:
                try:
                    with open(self.cookies_file, 'r') as file:
                        cookies = json.load(file)
                        context.add_cookies(cookies)
                        logger.info(f"Loaded cookies from {self.cookies_file}")
                except (FileNotFoundError, json.JSONDecodeError) as e:
                    logger.error(f"Failed to load cookies from {self.cookies_file}: {str(e)}")
                    # Continue without cookies rather than failing completely
            
            return context
            
        except Exception as e:
            logger.error(f"Failed to initialize Playwright driver: {str(e)}")
            # Clean up partially initialized resources
            self.close_resources()
            raise

    def _get_user_agent(self, user_agent_type: str) -> str:
        """
        Get a user agent string based on the specified type.
        
        Args:
            user_agent_type: Type of user agent to use ("default", "random", or "mobile")
            
        Returns:
            A user agent string
        """
        # Default Chrome user agent
        default_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        
        # Collection of desktop user agents
        desktop_uas = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 OPR/108.0.0.0",
        ]
        
        # Collection of mobile user agents
        mobile_uas = [
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPad; CPU OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Linux; Android 13; SM-S901B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.90 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.90 Mobile Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/122.0.6261.89 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.90 Mobile Safari/537.36",
        ]
        
        if user_agent_type == "default":
            return default_ua
        elif user_agent_type == "random":
            # Pick a random desktop user agent
            import random
            return random.choice(desktop_uas)
        elif user_agent_type == "mobile":
            # Pick a random mobile user agent
            import random
            return random.choice(mobile_uas)
        else:
            logger.warning(f"Unknown user agent type: {user_agent_type}, using default")
            return default_ua
    
    def close(self, context: BrowserContext) -> None:
        """
        Close the browser context and clean up resources.
        
        Args:
            context: The browser context to close.
        """
        try:
            if context:
                context.close()
            self.close_resources()
            logger.info("Playwright driver closed successfully")
        except Exception as e:
            logger.error(f"Error when closing Playwright driver: {str(e)}")
    
    def close_resources(self) -> None:
        """Close browser and playwright instances if they exist."""
        try:
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except Exception as e:
            logger.error(f"Error when closing Playwright resources: {str(e)}")