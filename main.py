"""
Followers Tracker Main Application.

This is the main entry point for the Followers Tracker application.
It collects follower statistics from all platforms and submits them to Google Forms.
"""

import sys
import os
import time
import logging
import argparse
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Create necessary directories before setting up logging
os.makedirs("logs", exist_ok=True)
os.makedirs("data", exist_ok=True)

# Set up root logger before importing other modules
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"logs/followers_tracker_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Import services and utilities
from services.linkedin_profile import LinkedInProfileService
from services.linkedin_company import LinkedInCompanyService
from services.linkedin_newsletter import LinkedInNewsletterService
from services.twitter import TwitterService
from services.instagram import InstagramService
from services.facebook import FacebookProfileService
from services.kit import KitService
from services.youtube import YouTubeService
from services.threads import ThreadsProfileService
from utils.followers_submitter import FollowersSubmitter
from services.tiktok import TikTok
from utils.exceptions import (
    ScrapingError, APIError, RateLimitError, DataSubmissionError
)
from config.settings import (
    AIFC_LKD_PAGE, BI_LKD_PAGE, NBO_LKD_PAGE, EXCEL_CHEATSHEETS_LKD_PAGE, FACEBOOK_URL,
    INSTAGRAM_USERNAME, INSTAGRAM_USERNAME_AIFC
)

def collect_linkedin_profile_data() -> Dict[str, Any]:
    """
    Collect data from LinkedIn personal profile.

    Returns:
        Dictionary with profile data
    """
    logger.info("Collecting LinkedIn profile data...")

    try:
        service = LinkedInProfileService()
        data = service.get_profile_data()

        logger.info(f"LinkedIn profile data collected: {data['followers']} followers")
        return data

    except Exception as e:
        logger.error(f"Failed to collect LinkedIn profile data: {str(e)}")
        return {
            "platform": "LinkedIn",
            "type": "Personal Profile",
            "followers": "Not Found",
            "error": str(e),
            "timestamp": time.time()
        }

def collect_linkedin_company_data() -> List[Dict[str, Any]]:
    """
    Collect data from LinkedIn company pages.

    Returns:
        List of dictionaries with company data
    """
    logger.info("Collecting LinkedIn company data...")

    company_urls = [
        AIFC_LKD_PAGE,
        BI_LKD_PAGE,
        NBO_LKD_PAGE,
        EXCEL_CHEATSHEETS_LKD_PAGE
    ]

    try:
        service = LinkedInCompanyService(company_urls)
        data = service.get_all_company_data()

        for company in data:
            logger.info(f"LinkedIn company data collected for {company['name']}: {company['followers']} followers")

        return data

    except Exception as e:
        logger.error(f"Failed to collect LinkedIn company data: {str(e)}")

        return [
            {
                "platform": "LinkedIn",
                "type": "Company Page",
                "name": name,
                "followers": "Not Found",
                "error": str(e),
                "timestamp": time.time()
            }
            for name in [
                "AI Finance Club",
                "Business Infographics",
                "Nicolas Boucher Online",
                "Excel Cheatsheets"
            ]
        ]

def collect_linkedin_newsletter_data() -> Dict[str, Any]:
    """
    Collect data from LinkedIn newsletter.

    Returns:
        Dictionary with newsletter data
    """
    logger.info("Collecting LinkedIn newsletter data...")

    try:
        service = LinkedInNewsletterService()
        data = service.get_newsletter_data()

        logger.info(f"LinkedIn newsletter data collected: {data['subscribers']} subscribers")
        return data

    except Exception as e:
        logger.error(f"Failed to collect LinkedIn newsletter data: {str(e)}")
        return {
            "platform": "LinkedIn",
            "type": "Newsletter",
            "subscribers": "Not Found",
            "error": str(e),
            "timestamp": time.time()
        }

def collect_twitter_data() -> Dict[str, Any]:
    """
    Collect data from Twitter.

    Returns:
        Dictionary with Twitter data
    """
    logger.info("Collecting Twitter data...")

    try:
        service = TwitterService()
        data = service.get_account_data()

        logger.info(f"Twitter data collected: {data['followers']} followers")
        return data

    except Exception as e:
        logger.error(f"Failed to collect Twitter data: {str(e)}")
        return {
            "platform": "Twitter",
            "followers": "Not Found",
            "error": str(e),
            "timestamp": time.time()
        }

def collect_instagram_data() -> Dict[str, Dict[str, Any]]:
    """
    Collect data for ALL Instagram profiles in a single browser session.

    Returns:
        Dictionary with keys 'personal' and 'aifc', each containing
        the follower data for that profile.
    """
    logger.info("Collecting Instagram data (personal + AI Finance Club)...")

    def _fallback(username: str) -> Dict[str, Any]:
        return {
            "platform": "Instagram",
            "username": username,
            "followers": "Not Found",
            "timestamp": time.time()
        }

    try:
        service = InstagramService()
        results = service.get_followers_bulk([
            INSTAGRAM_USERNAME,
            INSTAGRAM_USERNAME_AIFC
        ])

        personal = results.get(INSTAGRAM_USERNAME) or _fallback(INSTAGRAM_USERNAME)
        aifc = results.get(INSTAGRAM_USERNAME_AIFC) or _fallback(INSTAGRAM_USERNAME_AIFC)

        # Normalize None -> "Not Found" so downstream stays consistent
        for profile in (personal, aifc):
            if profile.get("followers") is None:
                profile["followers"] = "Not Found"

        logger.info(f"Instagram personal ({INSTAGRAM_USERNAME}): {personal['followers']} followers")
        logger.info(f"Instagram AIFC ({INSTAGRAM_USERNAME_AIFC}): {aifc['followers']} followers")

        return {"personal": personal, "aifc": aifc}

    except Exception as e:
        logger.error(f"Failed to collect Instagram data: {str(e)}")
        personal = _fallback(INSTAGRAM_USERNAME)
        aifc = _fallback(INSTAGRAM_USERNAME_AIFC)
        personal["error"] = str(e)
        aifc["error"] = str(e)
        return {"personal": personal, "aifc": aifc}

def collect_facebook_data() -> Dict[str, Any]:
    """
    Collect data from Facebook.

    Returns:
        Dictionary with Facebook data
    """
    logger.info("Collecting Facebook data...")

    try:
        service = FacebookProfileService()
        followers_count = service.get_followers()

        logger.info(f"Facebook data collected: {followers_count} followers")
        return {
            "platform": "Facebook",
            "followers": followers_count,
            "error": None,
            "timestamp": time.time()
        }

    except Exception as e:
        logger.error(f"Failed to collect Facebook data: {str(e)}")
        return {
            "platform": "Facebook",
            "followers": "Not Found",
            "error": str(e),
            "timestamp": time.time()
        }

def collect_youtube_data() -> Dict[str, Any]:
    """
    Collect data from YouTube.

    Returns:
        Dictionary with YouTube data
    """
    logger.info("Collecting YouTube data...")

    try:
        service = YouTubeService()
        data = service.get_channel_stats()

        if isinstance(data.get("subscribers"), int) and isinstance(data.get("views"), int):
            logger.info(f"YouTube data collected: {data['subscribers']} subscribers, {data['views']} views")
        else:
            logger.warning("YouTube data collection failed or returned invalid data")

        return data

    except Exception as e:
        logger.error(f"Failed to collect YouTube data: {str(e)}")
        return {
            "platform": "YouTube",
            "subscribers": "Not Found",
            "views": "Not Found",
            "error": str(e),
            "timestamp": time.time()
        }

def collect_kit_data() -> Dict[str, Dict[str, Any]]:
    """
    Collect data from Kit.

    Returns:
        Dictionary with Kit data for daily, weekly, and monthly stats
    """
    logger.info("Collecting Kit data...")

    try:
        service = KitService()
        data = service.get_all_stats()

        logger.info(f"Kit data collected: {data['daily']['subscribers']} daily subscribers")
        return data

    except Exception as e:
        logger.error(f"Failed to collect Kit data: {str(e)}")
        return {
            time_range: {
                "platform": "Kit",
                "time_range": time_range,
                "subscribers": "Not Found",
                "error": str(e),
                "timestamp": time.time()
            }
            for time_range in ["daily", "weekly", "monthly"]
        }

def collect_tiktok_data():
    logger.info("Collecting Tiktok Data..")

    try:
        service = TikTok()
        data = service.get_metrics()
        return data
    except Exception as e:
        logger.error(f"Failed to retrieve Tiktok's information. Check {e}")
        return None

def collect_threads_data() -> Dict[str, Any]:
    logger.info("Collecting Threads data...")

    try:
        service = ThreadsProfileService()
        data = service.get_profile_data()

        logger.info(f"Threads data collected: {data['followers']} followers")
        return data

    except Exception as e:
        logger.error(f"Failed to collect Threads data: {str(e)}")
        return {
            "platform": "Threads",
            "followers": "Not Found",
            "error": str(e),
            "timestamp": time.time()
        }

def submit_data(
    linkedin_profile_data: Dict[str, Any],
    linkedin_company_data: List[Dict[str, Any]],
    linkedin_newsletter_data: Dict[str, Any],
    twitter_data: Dict[str, Any],
    instagram_data: Dict[str, Any],
    instagram_aifc_data: Dict[str, Any],
    facebook_data: Dict[str, Any],
    youtube_data: Dict[str, Any],
    tiktok_data,
    threads_data,
    kit_data: Dict[str, Dict[str, Any]],
) -> bool:
    """
    Submit collected data to Google Forms.

    Args:
        linkedin_profile_data: LinkedIn profile data
        linkedin_company_data: LinkedIn company data
        linkedin_newsletter_data: LinkedIn newsletter data
        twitter_data: Twitter data
        instagram_data: Personal Instagram profile data
        instagram_aifc_data: AI Finance Club Instagram profile data
        facebook_data: Facebook data
        youtube_data: YouTube data
        tiktok_data: TikTok data
        threads_data: Threads data
        kit_data: Kit data

    Returns:
        True if all submissions were successful, False otherwise
    """
    logger.info("Submitting data to Google Forms...")

    try:
        submitter = FollowersSubmitter()

        # Submit followers data
        followers_success = submitter.submit_followers_data(
            linkedin_profile_data,
            linkedin_company_data,
            linkedin_newsletter_data,
            youtube_data,
            instagram_data,
            instagram_aifc_data,
            facebook_data,
            twitter_data,
            tiktok_data,
            threads_data,
            kit_data["daily"]
        )

        # Submit Kit stats data
        kit_success = submitter.submit_kit_stats(
            kit_data["daily"],
            kit_data["weekly"],
            kit_data["monthly"]
        )

        if followers_success and kit_success:
            logger.info("All data successfully submitted to Google Forms")
            return True
        else:
            if not followers_success:
                logger.error("Failed to submit followers data")
            if not kit_success:
                logger.error("Failed to submit Kit stats data")
            return False

    except Exception as e:
        logger.error(f"Error during data submission: {str(e)}")
        return False

def run_followers_tracker():
    """
    Run the complete followers tracker process.

    This function orchestrates the entire process of collecting and submitting data.
    """
    logger.info("Starting Followers Tracker")
    start_time = time.time()

    try:
        # Step 1: Collect data from all platforms
        linkedin_profile_data = collect_linkedin_profile_data()
        linkedin_company_data = collect_linkedin_company_data()
        linkedin_newsletter_data = collect_linkedin_newsletter_data()
        twitter_data = collect_twitter_data()
        instagram_results = collect_instagram_data()  # both profiles, one call
        facebook_data = collect_facebook_data()
        youtube_data = collect_youtube_data()
        tiktok_data = collect_tiktok_data()
        threads_data = collect_threads_data()
        kit_data = collect_kit_data()

        # Step 2: Submit data to Google Forms
        submission_success = submit_data(
            linkedin_profile_data,
            linkedin_company_data,
            linkedin_newsletter_data,
            twitter_data,
            instagram_results["personal"],
            instagram_results["aifc"],
            facebook_data,
            youtube_data,
            tiktok_data,
            threads_data,
            kit_data
        )

        # Calculate execution time
        execution_time = time.time() - start_time

        if submission_success:
            logger.info(f"Followers Tracker completed successfully in {execution_time:.2f} seconds")
        else:
            logger.warning(f"Followers Tracker completed with errors in {execution_time:.2f} seconds")

        return submission_success

    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"Followers Tracker failed with error: {str(e)}")
        logger.error(f"Execution time before failure: {execution_time:.2f} seconds")
        return False

def parse_arguments():
    """
    Parse command line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description='Followers Tracker')

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging (DEBUG level)'
    )

    parser.add_argument(
        '--log-file',
        type=str,
        default=None,
        help='Path to log file (default: logs/followers_tracker_[timestamp].log)'
    )

    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")

    if args.log_file:
        file_handler = logging.FileHandler(args.log_file)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(file_handler)
        logger.info(f"Logging to file: {args.log_file}")

    success = run_followers_tracker()

    sys.exit(0 if success else 1)