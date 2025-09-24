"""
Central configuration settings for the followers tracker application.

This module contains all the configuration variables used across the application,
including URLs, API endpoints, paths, and other settings.
"""

import os
from pathlib import Path
from dotenv import load_dotenv


ENV_FILE_PATH = os.getenv('ENV_PATH', 'config/.env')
load_dotenv(ENV_FILE_PATH)

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# LinkedIn URLs
NICOLAS_LKD_PROFILE = 'https://de.linkedin.com/in/bouchernicolas'
LKD_NEWSLETTER = 'https://www.linkedin.com/pulse/1-reason-your-month-end-close-failing-how-fix-nicolas-boucher-utgpf?trk=news-guest_share-article'
AIFC_LKD_PAGE = 'https://www.linkedin.com/company/ai-finance-club'
BI_LKD_PAGE = 'https://www.linkedin.com/company/business-infographics'
NBO_LKD_PAGE = 'https://www.linkedin.com/company/nicolas-boucher-online'
EXCEL_CHEATSHEETS_LKD_PAGE = 'https://www.linkedin.com/company/excel-cheatsheets/'

#Instagram Account
INSTAGRAM_PROFILE_URL = 'https://www.instagram.com/nicolasboucherfinance/'
INSTAGRAM_MAX_RETRIES = 10

# Twitter settings
TWITTER_USERNAME = 'bouchernicolas'
TWITTER_BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN')

# YouTube settings
YT_CHANNEL_ID = os.getenv('YOUTUBE_CHANNEL_ID')
YT_API_KEY = os.getenv('YOUTUBE_API_ID')

# Instagram settings
INSTAGRAM_USERNAME = 'nicolasboucherfinance'

# Kit settings
KIT_API_KEY = os.getenv('KIT_V4_API_KEY')
KIT_GROWTH_STATS_ENDPOINT = "https://api.kit.com/v4/account/growth_stats"

# API endpoints
YOUTUBE_STATS_ENDPOINT = f'https://www.googleapis.com/youtube/v3/channels?part=statistics&id={YT_CHANNEL_ID}&key={YT_API_KEY}'
TWITTER_API_ENDPOINT = f"https://api.twitter.com/2/users/by/username/{TWITTER_USERNAME}?user.fields=public_metrics"
INSTAGRAM_API_ENDPOINT = "https://fanhub.pro/tucktools_user"
KIT_GROWTH_STATS_ENDPOINT = "https://api.kit.com/v4/account/growth_stats"

# Google Form URLs
FOLLOWERS_FORM_URL = 'https://docs.google.com/forms/d/e/1FAIpQLSeK_A8x_7ipnICGwK3k3MdTq3vGhXwfu9BhSz37Bgz27T1llw/formResponse'
KIT_STATS_FORM_URL = 'https://docs.google.com/forms/d/e/1FAIpQLSfOM3yefdvcyb3lXFlJqH0ZFUSaQ2lFvUGnDlgt7ELB0-ChMg/formResponse'

# Google Form fields mapping
FOLLOWERS_FORM_FIELDS = {
    'Business Infographics': 'entry.1247179473',
    'Nicolas Boucher Online': 'entry.1150066733',
    'AI Finance Club': 'entry.269674828',
    'Excel Cheatsheets' :'entry.112291860',
    'Nicolas Boucher Personal Account': 'entry.627780398',
    'AI + Finance by Nicolas Boucher Newsteller': 'entry.508828894',
    'Nicolas Boucher Online Videos | YouTube Subscribers': 'entry.114799247',
    'Nicolas Boucher Online Videos | YouTube Total Views': 'entry.1433952907',
    'Instagram Total Followers': 'entry.147129590',
    'X Total Number of Followers': 'entry.121881511',
    "Kit's Daily Number of Subscribers": 'entry.395742871'
}

KIT_STATS_FORM_FIELDS = {
    "Today's Number of Subs": 'entry.1792758135',
    "Cancellation": 'entry.228306667',
    "Net New Subscribers": 'entry.862964481',
    "New Subscribers": 'entry.1339230177',
    "Weekly Number of Subscribers": 'entry.1849968148',
    "Weekly Cancellations": 'entry.15667906',
    "Weekly Net New Subscribers": 'entry.1685405274',
    "Weekly New Subscribers": 'entry.1145101214',
    "Monthly Number of Subs": 'entry.1509411799',
    "Monthly Cancellations": 'entry.759665711',
    "Monthly Net New Subscribers": 'entry.1932265942',
    "Monthly New Subscribers": 'entry.2091527192'
}

LOG_FILE_PATH = os.getenv('LOG_FILE_PATH', 'logs/followers_tracker.log')


# Database settings
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///data/followers_stats.db')

# General settings
DEFAULT_TIMEOUT = int(os.getenv('DEFAULT_TIMEOUT', '30'))  # Default timeout in seconds
MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))  # Default max retries
HEADLESS_BROWSER = os.getenv('HEADLESS_BROWSER', 'False').lower() == 'false'
