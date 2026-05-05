import sys, os, re, json, time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.playwright_driver import PlaywrightDriver

class TikTok:
    def __init__(self):
        self.base_url = 'https://www.tiktok.com/@nicolasboucherofficial?_r=1&_t=ZS-92tjkJvDnZB'
        self.cookies_file = r'tiktok.json'

    def get_metrics(self):
        """Fetch TikTok followers and likes using Playwright."""
        driver = PlaywrightDriver(cookies_file=self.cookies_file)
        context = driver.initialize_driver()
        page = context.new_page()

        try:
            page.goto(self.base_url, timeout=2000000)
            time.sleep(15)  

            page_content = page.content()

            counts = self.extract_user_interaction_counts(page_content)

            if counts:
                likes, followers = counts
                print(f"✅ Followers: {followers}")
                print(f"✅ Total Likes: {likes}")

                return {"followers": followers, "likes": likes}
            else:
                print("❌ Could not find follower or like count.")
                return None

        except Exception as e:
            print(f"❌ Error in TikTok scraping: {e}")
            return None

        finally:
            driver.close(context)  

    def extract_user_interaction_counts(self, page_content=None):
        """Extract likes and followers from TikTok page content."""
        if not page_content:
            print("⚠️ No page content provided to extract_user_interaction_counts.")
            return None

        try:
            matches = re.findall(r'"userInteractionCount":(\d+)', page_content)
            if len(matches) >= 2:
                return int(matches[0]), int(matches[1]) 

        except Exception as e:
            print(f"❌ Error extracting counts: {e}")
        return None

if __name__ == "__main__":
    tiktok = TikTok()
    metrics = tiktok.get_metrics()
    print(metrics)
