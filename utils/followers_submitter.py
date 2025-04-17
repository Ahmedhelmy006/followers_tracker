"""
Followers Submitter utility.

This module handles collecting follower data from all services and
submitting it to Google Forms.
"""

import logging
import time
from typing import Dict, Any, List, Optional

from config.settings import (
    FOLLOWERS_FORM_URL,
    FOLLOWERS_FORM_FIELDS,
    KIT_STATS_FORM_URL,
    KIT_STATS_FORM_FIELDS
)
from utils.forms_submitter import GoogleFormsSubmitter
from utils.exceptions import DataSubmissionError

logger = logging.getLogger(__name__)

class FollowersSubmitter:
    """
    Utility for collecting follower data and submitting it to Google Forms.
    
    This class handles mapping data from all services to the appropriate form fields
    and submitting the data to the configured Google Forms.
    """
    
    def __init__(self):
        """Initialize the FollowersSubmitter."""
        # Create form submitters
        self.followers_form_submitter = GoogleFormsSubmitter(
            FOLLOWERS_FORM_URL,
            FOLLOWERS_FORM_FIELDS
        )
        
        self.kit_stats_form_submitter = GoogleFormsSubmitter(
            KIT_STATS_FORM_URL,
            KIT_STATS_FORM_FIELDS
        )
        
        logger.info("FollowersSubmitter initialized")
    
    def submit_followers_data(self, 
                             linkedin_profile_data: Dict[str, Any],
                             linkedin_company_data: List[Dict[str, Any]],
                             linkedin_newsletter_data: Dict[str, Any],
                             youtube_data: Dict[str, Any],
                             instagram_data: Dict[str, Any],
                             twitter_data: Dict[str, Any],
                             kit_data: Dict[str, Any]) -> bool:
        """
        Submit followers data to the followers form.
        
        Args:
            linkedin_profile_data: Data from LinkedIn profile service
            linkedin_company_data: Data from LinkedIn company service
            linkedin_newsletter_data: Data from LinkedIn newsletter service
            youtube_data: Data from YouTube service
            instagram_data: Data from Instagram service
            twitter_data: Data from Twitter service
            kit_data: Data from Kit service daily stats
            
        Returns:
            True if submission was successful, False otherwise
            
        Raises:
            DataSubmissionError: If there is an error mapping or submitting the data
        """
        try:
            # Map company data by name
            company_data_by_name = {}
            for company in linkedin_company_data:
                company_data_by_name[company.get("name")] = company
            
            # Map all data to form fields
            form_data = {
                # LinkedIn Profile Data
                'Nicolas Boucher Personal Account': linkedin_profile_data.get("followers"),
                
                # LinkedIn Company Data
                'Business Infographics': company_data_by_name.get("Business Infographics", {}).get("followers"),
                'Nicolas Boucher Online': company_data_by_name.get("Nicolas Boucher Online", {}).get("followers"),
                'AI Finance Club': company_data_by_name.get("Ai Finance Club", {}).get("followers"),
                'Excel Cheatsheets': company_data_by_name.get("Excel Cheatsheets", {}).get("followers"),
                
                # LinkedIn Newsletter Data
                'AI + Finance by Nicolas Boucher Newsteller': linkedin_newsletter_data.get("subscribers"),
                
                # YouTube Data
                'Nicolas Boucher Online Videos | YouTube Subscribers': youtube_data.get("subscribers"),
                'Nicolas Boucher Online Videos | YouTube Total Views': youtube_data.get("views"),
                
                # Instagram Data
                'Instagram Total Followers': instagram_data.get("followers"),
                
                # Twitter Data
                'X Total Number of Followers': twitter_data.get("followers"),
                'X Followers Last 30 Days': twitter_data.get("followers_last_30_days", "Not Available"),
                'X Followers Last 30 Days Percentage': twitter_data.get("followers_percentage", "Not Available"),
                
                # Kit Data
                "Kit's Daily Number of Subscribers": kit_data.get("subscribers")
            }
            
            # Log the mapped data
            logger.info("Mapped followers data for form submission")
            logger.debug(f"Form data: {form_data}")
            
            # Submit the data
            success = self.followers_form_submitter.submit_data(form_data)
            
            if success:
                logger.info("Successfully submitted followers data to Google Form")
            else:
                logger.error("Failed to submit followers data to Google Form")
                
            return success
            
        except Exception as e:
            error_msg = f"Error submitting followers data: {str(e)}"
            logger.error(error_msg)
            raise DataSubmissionError(error_msg)
    
    def submit_kit_stats(self, kit_daily: Dict[str, Any], 
                         kit_weekly: Dict[str, Any], 
                         kit_monthly: Dict[str, Any]) -> bool:
        """
        Submit Kit statistics to the Kit stats form.
        
        Args:
            kit_daily: Daily Kit stats
            kit_weekly: Weekly Kit stats
            kit_monthly: Monthly Kit stats
            
        Returns:
            True if submission was successful, False otherwise
            
        Raises:
            DataSubmissionError: If there is an error mapping or submitting the data
        """
        try:
            # Map Kit stats to form fields
            form_data = {
                "Today's Number of Subs": kit_daily.get("subscribers"),
                "Cancellation": kit_daily.get("cancellations"),
                "Net New Subscribers": kit_daily.get("net_new_subscribers"),
                "New Subscribers": kit_daily.get("new_subscribers"),
                
                "Weekly Number of Subscribers": kit_weekly.get("subscribers"),
                "Weekly Cancellations": kit_weekly.get("cancellations"),
                "Weekly Net New Subscribers": kit_weekly.get("net_new_subscribers"),
                "Weekly New Subscribers": kit_weekly.get("new_subscribers"),
                
                "Monthly Number of Subs": kit_monthly.get("subscribers"),
                "Monthly Cancellations": kit_monthly.get("cancellations"),
                "Monthly Net New Subscribers": kit_monthly.get("net_new_subscribers"),
                "Monthly New Subscribers": kit_monthly.get("new_subscribers")
            }
            
            # Log the mapped data
            logger.info("Mapped Kit stats data for form submission")
            logger.debug(f"Form data: {form_data}")
            
            # Submit the data
            success = self.kit_stats_form_submitter.submit_data(form_data)
            
            if success:
                logger.info("Successfully submitted Kit stats to Google Form")
            else:
                logger.error("Failed to submit Kit stats to Google Form")
                
            return success
            
        except Exception as e:
            error_msg = f"Error submitting Kit stats: {str(e)}"
            logger.error(error_msg)
            raise DataSubmissionError(error_msg)