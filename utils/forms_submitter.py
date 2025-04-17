import requests
import logging
from typing import Dict, Any, Optional, Union
import time

logger = logging.getLogger(__name__)

class GoogleFormsSubmitter:
    """
    A utility class to submit data to Google Forms.
    
    This class handles mapping data fields to form fields and submitting the data.
    """
    
    def __init__(self, form_url: str, form_fields: Dict[str, str], timeout: int = 30):
        """
        Initialize the GoogleFormsSubmitter.
        
        Args:
            form_url: The URL of the Google Form to submit data to.
            form_fields: A dictionary mapping data keys to form field names.
            timeout: Request timeout in seconds.
        """
        self.form_url = form_url
        self.form_fields = form_fields
        self.timeout = timeout
    
    def submit_data(self, data: Dict[str, Any], max_retries: int = 3) -> bool:
        """
        Submit data to the Google Form.
        
        Args:
            data: A dictionary containing the data to submit.
            max_retries: Maximum number of retry attempts for failed submissions.
            
        Returns:
            True if submission was successful, False otherwise.
        """
        # Map data to form fields
        form_data = {self.form_fields[key]: value 
                    for key, value in data.items() 
                    if key in self.form_fields}
        
        # Log what's being submitted (without sensitive data)
        logger.info(f"Submitting data to Google Form: {self.form_url}")
        logger.debug(f"Form fields being submitted: {list(form_data.keys())}")
        
        # Track retries
        retries = 0
        
        while retries <= max_retries:
            try:
                response = requests.post(
                    self.form_url, 
                    data=form_data,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    logger.info("Data successfully submitted to Google Form!")
                    return True
                else:
                    logger.warning(f"Failed to submit data. Status code: {response.status_code}")
                    if retries == max_retries:
                        logger.error("Maximum retry attempts reached.")
                        return False
                    retries += 1
                    # Exponential backoff
                    time.sleep(2 ** retries)
                    logger.info(f"Retrying submission (attempt {retries}/{max_retries})...")
                    
            except requests.RequestException as e:
                logger.error(f"Request error when submitting to Google Form: {str(e)}")
                if retries == max_retries:
                    return False
                retries += 1
                # Exponential backoff
                time.sleep(2 ** retries)
                logger.info(f"Retrying submission (attempt {retries}/{max_retries})...")
        
        return False