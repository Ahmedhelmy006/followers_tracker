"""
Configuration package for the followers tracker application.

This package contains configuration modules that provide settings,
constants, and selectors used throughout the application.
"""

from config.settings import (
    # URLs
    NICOLAS_LKD_PROFILE,
    LKD_NEWSLETTER,
    AIFC_LKD_PAGE,
    BI_LKD_PAGE,
    NBO_LKD_PAGE,
    EXCEL_CHEATSHEETS_LKD_PAGE,
    
    # API endpoints
    YOUTUBE_STATS_ENDPOINT,
    TWITTER_API_ENDPOINT,
    INSTAGRAM_API_ENDPOINT,
    KIT_GROWTH_STATS_ENDPOINT,
    
    # Form URLs
    FOLLOWERS_FORM_URL,
    KIT_STATS_FORM_URL,
    
    # Path settings
    LOG_FILE_PATH,
    
    # Environment settings
    ENV_FILE_PATH,
    
    # Other settings
    DEFAULT_TIMEOUT,
    MAX_RETRIES
)



__all__ = [
    # URLs
    'NICOLAS_LKD_PROFILE',
    'LKD_NEWSLETTER',
    'AIFC_LKD_PAGE',
    'BI_LKD_PAGE',
    'NBO_LKD_PAGE',
    'EXCEL_CHEATSHEETS_LKD_PAGE',
    
    # API endpoints
    'YOUTUBE_STATS_ENDPOINT',
    'TWITTER_API_ENDPOINT',
    'INSTAGRAM_API_ENDPOINT',
    'KIT_GROWTH_STATS_ENDPOINT',
    
    # Form URLs
    'FOLLOWERS_FORM_URL',
    'KIT_STATS_FORM_URL',
    
    # Path settings
    'COOKIES_FILE_PATH',
    'LOG_FILE_PATH',
    
    # Environment settings
    'ENV_FILE_PATH',
    
    # Other settings
    'DEFAULT_TIMEOUT',
    'MAX_RETRIES',
    
    # Selector classes
    'LinkedInSelectors',
    'YouTubeSelectors',
    'TwitterSelectors'
]