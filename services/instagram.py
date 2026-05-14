import json
import time
import logging
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)

class InstagramService:
    
    def __init__(self, username: str):
        self.username = username
        self.follower_count = None

    def get_followers(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = context.new_page()

            # Intercept GraphQL responses
            def handle_response(response):
                if "graphql/query" in response.url and response.status == 200:
                    try:
                        data = response.json()
                        user = data.get("data", {}).get("user", {})
                        if "follower_count" in user:
                            self.follower_count = user["follower_count"]
                            logger.info(f"Follower count: {self.follower_count}")
                    except Exception as e:
                        logger.warning(f"Could not parse response: {e}")

            page.on("response", handle_response)

            # Visit the profile page to trigger the GraphQL call
            page.goto(f"https://www.instagram.com/{self.username}/", wait_until="networkidle")
            
            browser.close()

        return {
            "platform": "Instagram",
            "username": self.username,
            "followers": self.follower_count,
            "timestamp": time.time(),
            "source": "graphql_intercept"
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    service = InstagramService(username="nicolasboucherfinance")
    result = service.get_followers()
    print(result)