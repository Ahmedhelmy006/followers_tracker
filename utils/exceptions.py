"""
Custom exceptions for the followers_tracker application.
"""

class FollowersTrackerError(Exception):
    """Base exception for all followers tracker errors."""
    pass


class AuthenticationError(FollowersTrackerError):
    """Raised when authentication fails for a platform."""
    pass


class ScrapingError(FollowersTrackerError):
    """Raised when scraping or parsing content fails."""
    pass


class APIError(FollowersTrackerError):
    """Raised when an API request fails."""
    def __init__(self, message, status_code=None, response=None):
        self.status_code = status_code
        self.response = response
        super().__init__(message)


class ConfigurationError(FollowersTrackerError):
    """Raised when there's an issue with configuration settings."""
    pass


class DataSubmissionError(FollowersTrackerError):
    """Raised when data submission to external services fails."""
    pass


class DatabaseError(FollowersTrackerError):
    """Raised when database operations fail."""
    pass


class ValidationError(FollowersTrackerError):
    """Raised when data validation fails."""
    pass


class RateLimitError(APIError):
    """Raised when a rate limit is reached for an API."""
    pass