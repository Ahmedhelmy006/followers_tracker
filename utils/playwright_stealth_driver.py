"""
Enhanced Playwright driver with stealth mode and advanced anti-detection techniques.

This module provides a more robust browser automation solution that attempts to 
bypass LinkedIn's anti-scraping measures.
"""

from playwright.sync_api import sync_playwright, BrowserContext, Browser
import json
import logging
import random
import time
from typing import Optional, Dict, Any, List, Tuple

logger = logging.getLogger(__name__)

class PlaywrightStealthDriver:
    """
    A utility class to manage Playwright browser automation with stealth mode.
    
    This class implements advanced techniques to avoid detection as a bot.
    """
    
    def __init__(self, cookies_file: Optional[str] = None, proxy: Optional[str] = None):
        """
        Initialize the PlaywrightStealthDriver.
        
        Args:
            cookies_file: Path to a JSON file containing cookies for authentication.
            proxy: Optional proxy server to use (format: 'http://user:pass@host:port')
        """
        self.cookies_file = cookies_file
        self.proxy = proxy
        self.playwright = None
        self.browser = None
        
    def initialize_driver(self, stealth_mode: bool = True) -> BrowserContext:
        """
        Start the browser and initialize a new context with stealth mode.
        
        Args:
            stealth_mode: Whether to enable stealth mode to avoid detection
            
        Returns:
            A browser context object that can be used to create pages.
            
        Raises:
            Exception: If browser initialization fails.
        """
        try:
            self.playwright = sync_playwright().start()
            
            # Prepare browser launch options
            launch_options = {
                "headless": True,
                "args": [
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-infobars',
                    '--disable-dev-shm-usage',
                    '--disable-extensions',
                    '--disable-gpu',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--disable-site-isolation-trials',
                    '--ignore-certificate-errors',
                    '--disable-setuid-sandbox',
                    '--disable-web-security',
                    '--disable-notifications',
                    '--disable-popup-blocking'
                ]
            }
            
            # Add proxy if provided
            if self.proxy:
                launch_options["proxy"] = {
                    "server": self.proxy
                }
            
            # Launch the browser with options
            self.browser = self.playwright.chromium.launch(**launch_options)
            
            # Generate random fingerprint data
            user_agent = self._get_random_user_agent()
            viewport = self._get_random_viewport()
            
            # Create context with privacy options
            context_options = {
                "viewport": viewport,
                "user_agent": user_agent,
                "locale": "en-US",
                "timezone_id": random.choice([
                    "America/New_York", "America/Chicago", "America/Los_Angeles", 
                    "Europe/London", "Europe/Paris", "Europe/Berlin", "Asia/Tokyo"
                ]),
                "geolocation": self._get_random_geolocation(),
                "permissions": ["geolocation", "notifications"],
                "bypass_csp": True,
                "java_script_enabled": True,
                "has_touch": random.choice([True, False, False, False]),  # 25% touch devices
                "is_mobile": random.choice([True, False, False, False, False]),  # 20% mobile
                "color_scheme": random.choice(["light", "dark", "light", "light"]),  # 75% light mode
            }
            
            context = self.browser.new_context(**context_options)
            
            # Set default timeout
            context.set_default_timeout(90000)  # 90 seconds
            
            # Apply stealth mode scripts if enabled
            if stealth_mode:
                self._apply_stealth_mode(context)
            
            # Add cookies if provided
            if self.cookies_file:
                try:
                    with open(self.cookies_file, 'r') as file:
                        cookies = json.load(file)
                        context.add_cookies(cookies)
                        logger.info(f"Loaded cookies from {self.cookies_file}")
                except (FileNotFoundError, json.JSONDecodeError) as e:
                    logger.error(f"Failed to load cookies from {self.cookies_file}: {str(e)}")
            
            logger.info(f"Browser initialized with stealth mode: {stealth_mode}")
            return context
            
        except Exception as e:
            logger.error(f"Failed to initialize Playwright driver: {str(e)}")
            # Clean up partially initialized resources
            self.close_resources()
            raise
    
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
    
    def _apply_stealth_mode(self, context: BrowserContext) -> None:
        """
        Apply stealth mode scripts to the browser context.
        
        Args:
            context: The browser context to apply stealth scripts to.
        """
        # Create a new page to apply stealth scripts globally
        page = context.new_page()
        
        # Mask WebDriver presence
        page.add_init_script("""
        () => {
            // Overwrite navigator properties to hide webdriver
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false,
                configurable: true
            });
            
            // Hide automation-related properties
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => {
                if (parameters.name === 'notifications') {
                    return Promise.resolve({state: Notification.permission});
                }
                return originalQuery(parameters);
            };
            
            // Modify user agent data to appear more natural
            if (navigator.userAgentData) {
                Object.defineProperty(navigator.userAgentData, 'brands', {
                    get: () => [
                        { brand: 'Chromium', version: '122' },
                        { brand: 'Google Chrome', version: '122' },
                        { brand: 'Not;A=Brand', version: '8' }
                    ]
                });
                
                Object.defineProperty(navigator.userAgentData, 'mobile', {
                    get: () => false
                });
            }
            
            // Add missing chrome object properties
            if (!window.chrome) {
                window.chrome = {};
            }
            
            if (!window.chrome.runtime) {
                window.chrome.runtime = {};
            }
        }
        """)
        
        # Add plugins array
        page.add_init_script("""
        () => {
            const makePlugin = (name, filename, description, version) => ({
                name, filename, description, version,
                length: 1,
                item: () => this,
                namedItem: () => this
            });
            
            // Create a fake plugins array with common plugins
            const plugins = [
                makePlugin('Chrome PDF Plugin', 'internal-pdf-viewer', 'Portable Document Format', '1.0'),
                makePlugin('Chrome PDF Viewer', 'mhjfbmdgcfjbbpaeojofohoefgiehjai', 'Portable Document Format', '1.0'),
                makePlugin('Native Client', 'internal-nacl-plugin', '', ''),
            ];
            
            // Override navigator.plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => {
                    plugins.refresh = () => {};
                    plugins.length = plugins.length;
                    plugins.item = (i) => plugins[i] || null;
                    plugins.namedItem = (name) => plugins.find(p => p.name === name) || null;
                    return plugins;
                }
            });
        }
        """)
        
        # Add Canvas and WebGL fingerprint evasion
        page.add_init_script("""
        () => {
            // Canvas fingerprint protection
            const originalGetContext = HTMLCanvasElement.prototype.getContext;
            HTMLCanvasElement.prototype.getContext = function(contextType, ...args) {
                const context = originalGetContext.call(this, contextType, ...args);
                if (context && (contextType === '2d' || contextType.includes('webgl'))) {
                    const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
                    
                    this.toDataURL = function(...toArgs) {
                        // Small random noise to canvas fingerprint
                        if (contextType === '2d') {
                            const r = Math.floor(Math.random() * 10) % 2;
                            if (r === 0) {
                                context.fillStyle = 'rgba(255, 255, 255, 0.0001)';
                                context.fillRect(0, 0, 1, 1);
                            }
                        }
                        return originalToDataURL.apply(this, toArgs);
                    };
                }
                return context;
            };
        }
        """)
        
        # Close the temporary page
        page.close()
        
        logger.debug("Applied stealth mode scripts to browser context")

    def _get_random_user_agent(self) -> str:
        """Get a random user agent string that appears legitimate."""
        user_agents = [
            # Chrome
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            
            # Firefox
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:123.0) Gecko/20100101 Firefox/123.0",
            "Mozilla/5.0 (X11; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0",
            
            # Safari
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
            
            # Edge
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
        ]
        return random.choice(user_agents)
    
    def _get_random_viewport(self) -> Dict[str, int]:
        """Get a random viewport size that appears legitimate."""
        viewports = [
            {"width": 1920, "height": 1080},  # Full HD
            {"width": 1366, "height": 768},   # Common laptop
            {"width": 1536, "height": 864},   # Common laptop HiDPI
            {"width": 1440, "height": 900},   # MacBook display
            {"width": 1680, "height": 1050},  # MacBook Pro
            {"width": 1280, "height": 720},   # HD
            {"width": 1280, "height": 800},   # MacBook
            {"width": 2560, "height": 1440},  # 2K
            {"width": 1600, "height": 900},   # HD+
        ]
        return random.choice(viewports)
    
    def _get_random_geolocation(self) -> Dict[str, float]:
        """Get a random geolocation within the continental US."""
        # Continental US boundaries (roughly)
        min_lat, max_lat = 24.0, 49.0
        min_lng, max_lng = -125.0, -66.0
        
        # Generate random latitude and longitude
        latitude = round(random.uniform(min_lat, max_lat), 6)
        longitude = round(random.uniform(min_lng, max_lng), 6)
        
        return {
            "latitude": latitude,
            "longitude": longitude,
            "accuracy": round(random.uniform(5, 100), 2)  # GPS accuracy in meters
        }
    
    def create_page_with_wait(self, context: BrowserContext) -> Tuple[Any, bool]:
        """
        Create a new page with random wait times to appear more human.
        
        Args:
            context: Browser context to create page from
            
        Returns:
            Tuple containing page object and success flag
        """
        page = context.new_page()
        
        # Randomize wait times to appear more human
        time.sleep(random.uniform(0.5, 1.5))
        
        # Disable JavaScript rendering for heavy pages (optional)
        # Helps avoid detection but might break some sites
        if random.random() < 0.2:  # 20% chance
            page.context.route("**/*.{png,jpg,jpeg,webp,svg,gif}", lambda route: route.abort())
        
        # Add a page error handler
        errors_detected = False
        
        def on_page_error(error):
            nonlocal errors_detected
            logger.warning(f"Page error detected: {error}")
            errors_detected = True
            
        page.on("pageerror", on_page_error)
        
        return page, errors_detected