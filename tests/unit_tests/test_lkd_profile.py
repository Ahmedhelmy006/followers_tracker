"""
Test for LinkedIn Profile Service.

This script tests the LinkedInProfileService by running it 50 times sequentially
and tracking success and failure rates.
"""

import sys
import os
import time
import logging
from datetime import datetime

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from services.linkedin_profile import LinkedInProfileService
from utils.exceptions import ScrapingError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"linkedin_profile_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def test_linkedin_profile_service(iterations=50):
    """
    Test the LinkedIn Profile Service multiple times.
    
    Args:
        iterations: Number of times to run the test
        
    Returns:
        A tuple containing (success_count, failure_count, success_rate)
    """
    service = LinkedInProfileService()
    
    success_count = 0
    failure_count = 0
    results = []
    
    logger.info(f"Starting LinkedIn Profile Service test with {iterations} iterations")
    start_time = time.time()
    
    for i in range(1, iterations + 1):
        iteration_start = time.time()
        logger.info(f"Starting iteration {i}/{iterations}")
        
        try:
            data = service.get_profile_data()
            
            # Check if we got a valid follower count
            if data["followers"] != "Not Found" and data["followers"] is not None:
                success_count += 1
                status = "SUCCESS"
            else:
                failure_count += 1
                status = "FAILURE (No data)"
                
            results.append(data)
            
        except ScrapingError as e:
            failure_count += 1
            status = f"FAILURE: {str(e)}"
            logger.error(f"Iteration {i} failed: {str(e)}")
            
        except Exception as e:
            failure_count += 1
            status = f"FAILURE: Unexpected error: {str(e)}"
            logger.error(f"Iteration {i} failed with unexpected error: {str(e)}")
        
        iteration_time = time.time() - iteration_start
        logger.info(f"Iteration {i} completed in {iteration_time:.2f} seconds: {status}")
        
        # Small delay to prevent rate limiting
        time.sleep(1)
    
    # Calculate statistics
    total_time = time.time() - start_time
    success_rate = (success_count / iterations) * 100
    
    logger.info(f"Test completed in {total_time:.2f} seconds")
    logger.info(f"Success count: {success_count}/{iterations} ({success_rate:.2f}%)")
    logger.info(f"Failure count: {failure_count}/{iterations} ({100 - success_rate:.2f}%)")
    
    if success_count > 0 and len(results) > 0:
        # Log some sample data from a successful run
        successful_result = next((r for r in results if r["followers"] != "Not Found"), None)
        if successful_result:
            logger.info(f"Sample successful result: {successful_result}")
    
    return success_count, failure_count, success_rate

if __name__ == "__main__":
    test_linkedin_profile_service(50)