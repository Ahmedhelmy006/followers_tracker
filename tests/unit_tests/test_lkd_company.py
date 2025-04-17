"""
Test for LinkedIn Company Service.

This script tests the LinkedInCompanyService by running it on all company pages
and tracking success and failure rates.
"""

import sys
import os
import time
import logging
from datetime import datetime

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from services.linkedin_company import LinkedInCompanyService
from utils.exceptions import ScrapingError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"linkedin_company_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def test_linkedin_company_service(iterations=1):
    """
    Test the LinkedIn Company Service multiple times.
    
    Args:
        iterations: Number of times to run the complete test
        
    Returns:
        A tuple containing (total_companies, success_count, failure_count, success_rate)
    """
    service = LinkedInCompanyService()
    
    # Track total success and failure across all iterations
    total_companies = len(service.company_urls) * iterations
    total_success = 0
    total_failure = 0
    all_results = []
    
    logger.info(f"Starting LinkedIn Company Service test with {iterations} iterations")
    logger.info(f"Testing {len(service.company_urls)} company pages per iteration")
    
    start_time = time.time()
    
    for i in range(1, iterations + 1):
        logger.info(f"Starting iteration {i}/{iterations}")
        iteration_start = time.time()
        
        try:
            # Get data for all companies
            results = service.get_all_company_data()
            all_results.extend(results)
            
            # Count successes and failures
            for company_data in results:
                if company_data["followers"] != "Not Found" and isinstance(company_data["followers"], int):
                    total_success += 1
                    logger.info(f"Success: {company_data['name']} - {company_data['followers']} followers")
                else:
                    total_failure += 1
                    logger.warning(f"Failure: {company_data['name']} - No follower count found")
                    
        except Exception as e:
            logger.error(f"Iteration {i} failed with error: {str(e)}")
            # If the whole iteration fails, count all companies as failures
            total_failure += len(service.company_urls)
        
        iteration_time = time.time() - iteration_start
        logger.info(f"Iteration {i} completed in {iteration_time:.2f} seconds")
    
    # Calculate final statistics
    total_time = time.time() - start_time
    success_rate = (total_success / total_companies) * 100 if total_companies > 0 else 0
    
    logger.info(f"Test completed in {total_time:.2f} seconds")
    logger.info(f"Total companies tested: {total_companies}")
    logger.info(f"Success count: {total_success}/{total_companies} ({success_rate:.2f}%)")
    logger.info(f"Failure count: {total_failure}/{total_companies} ({100 - success_rate:.2f}%)")
    
    # Log results per company
    if all_results:
        company_stats = {}
        
        for result in all_results:
            company_name = result['name']
            if company_name not in company_stats:
                company_stats[company_name] = {'success': 0, 'failure': 0}
            
            if result["followers"] != "Not Found" and isinstance(result["followers"], int):
                company_stats[company_name]['success'] += 1
            else:
                company_stats[company_name]['failure'] += 1
        
        logger.info("Results by company:")
        for company, stats in company_stats.items():
            company_success_rate = (stats['success'] / (stats['success'] + stats['failure'])) * 100
            logger.info(f"  {company}: {stats['success']}/{stats['success'] + stats['failure']} successful ({company_success_rate:.2f}%)")
    
    return total_companies, total_success, total_failure, success_rate

if __name__ == "__main__":
    # Run the test once to check all company pages
    test_linkedin_company_service(1)