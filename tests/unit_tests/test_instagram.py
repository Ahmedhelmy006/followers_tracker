"""
Test for Instagram Direct Scraping.

This script specifically tests the direct scraping fallback mechanism
of the InstagramService, bypassing the third-party API.
"""

import sys
import os
import time
import logging
from datetime import datetime
import unittest
from unittest.mock import patch, MagicMock

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from services.instagram import InstagramService
from utils.exceptions import ScrapingError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"instagram_scraping_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class TestInstagramScraping(unittest.TestCase):
    """Test case for Instagram direct scraping functionality."""
    
    def setUp(self):
        """Set up test case with an Instagram service instance."""
        self.service = InstagramService()
    
    @patch('services.instagram.InstagramService._get_followers_from_api')
    def test_direct_scraping(self, mock_api):
        """
        Test the direct scraping functionality by forcing API failure.
        
        This test patches the API method to always fail, forcing the service
        to use the direct scraping method instead.
        """
        # Mock the API method to always fail
        mock_api.return_value = {
            "success": False,
            "error": "Forced API failure for testing"
        }
        
        logger.info("Starting Instagram direct scraping test")
        start_time = time.time()
        
        # Get follower data, which should now use scraping
        data = self.service.get_followers()
        
        # Log the result
        if data.get("followers") != "Not Found" and data.get("followers") is not None:
            success = True
            followers_count = data.get("followers")
            source = data.get("source", "unknown")
            
            logger.info(f"Successfully retrieved {followers_count} followers via {source}")
            status = f"SUCCESS via {source}"
            
            # Verify the data was retrieved via scraping
            self.assertEqual(source, "direct-scraping", "Data should be retrieved via direct scraping")
            self.assertIsInstance(followers_count, int, "Follower count should be an integer")
            self.assertGreater(followers_count, 0, "Follower count should be greater than 0")
        else:
            success = False
            error = data.get("error", "Unknown error")
            
            logger.error(f"Failed to retrieve follower count: {error}")
            status = f"FAILURE: {error}"
            
            # If scraping failed, this test will fail
            self.fail(f"Direct scraping failed: {error}")
        
        # Calculate execution time
        execution_time = time.time() - start_time
        logger.info(f"Test completed in {execution_time:.2f} seconds: {status}")
        
        return success, followers_count, source
    
    def test_scraping_method_directly(self):
        """
        Test the _get_followers_from_scraping method directly.
        
        This calls the internal scraping method directly to verify it works.
        """
        logger.info("Testing the scraping method directly")
        start_time = time.time()
        
        # Call the scraping method directly
        result = self.service._get_followers_from_scraping()
        
        if result["success"]:
            logger.info(f"Scraping successful with {result['followers']} followers")
            self.assertIsInstance(result["followers"], int, "Follower count should be an integer")
            self.assertGreater(result["followers"], 0, "Follower count should be greater than 0")
        else:
            logger.error(f"Direct scraping method failed: {result.get('error')}")
            self.fail(f"Scraping method failed: {result.get('error')}")
        
        execution_time = time.time() - start_time
        logger.info(f"Direct scraping method test completed in {execution_time:.2f} seconds")
        
        return result["success"], result.get("followers")

def run_tests():
    """Run the Instagram scraping tests."""
    test_suite = unittest.TestSuite()
    test_suite.addTest(TestInstagramScraping('test_direct_scraping'))
    test_suite.addTest(TestInstagramScraping('test_scraping_method_directly'))
    
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(test_suite)

if __name__ == "__main__":
    run_tests()