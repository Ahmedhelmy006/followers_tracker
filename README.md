# Followers Tracker

A robust Python application that automatically tracks follower counts and subscriber statistics across multiple social media platforms, including LinkedIn, Twitter, Instagram, YouTube, and Kit.

## Overview

This application collects and reports follower statistics for:

- **LinkedIn** (profiles, company pages, newsletters)
- **Twitter/X**
- **Instagram**
- **YouTube**
- **Kit** (formerly ConvertKit)

Data is collected daily and submitted to Google Forms, allowing for easy tracking and visualization of follower growth over time.

## Features

- **Multi-platform support**: Collects data from five different platforms
- **Authentication-free operation**: Runs without requiring login credentials
- **Robust error handling**: Employs sophisticated retry mechanisms and fallbacks
- **Stealth techniques**: Implements advanced methods to avoid detection by anti-scraping systems
- **Extensive logging**: Provides detailed logs for monitoring and troubleshooting
- **Modular architecture**: Clean, maintainable code with well-separated concerns

## Project Structure

```
followers-tracker/
│
├── config/                 # Configuration settings
│   ├── __init__.py
│   ├── settings.py         # Central configuration
│   ├── selectors.py        # HTML/CSS selectors
│   └── env_handler.py      # Environment variable management
│
├── services/               # Platform-specific modules
│   ├── linkedin_profile.py
│   ├── linkedin_company.py
│   ├── linkedin_newsletter.py
│   ├── youtube.py
│   ├── twitter.py
│   ├── instagram.py
│   └── kit.py
│
├── utils/                  # Utility functions
│   ├── playwright_driver.py
│   ├── playwright_stealth_driver.py
│   ├── forms_submitter.py
│   ├── followers_submitter.py
│   ├── logger.py
│   └── exceptions.py
│
├── tests/                  # Test modules
│   └── unit_tests/
│
├── data/                   # Data storage
├── logs/                   # Log files
├── main.py                 # Main entry point
└── README.md               # This file
```

## Requirements

- Python 3.8+
- Playwright
- Required Python packages (see requirements.txt)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Ahmedhelmy006/followers_tracker.git
   cd followers_tracker
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install Playwright browsers:
   ```bash
   python -m playwright install chromium
   ```

4. Create a `.env` file in the `config` directory based on the provided template:
   ```bash
   cp config/.env.template config/.env
   ```

5. Update the `.env` file with your API keys and configurations.

## Usage

### Running the application

```bash
python main.py
```

### Command-line options

```bash
# For verbose (DEBUG) logging
python main.py --verbose

# With custom log file
python main.py --log-file custom_log.log
```

### Scheduled execution

For automated daily tracking, set up a cron job or scheduled task:

#### Linux (cron)
```bash
0 9 * * * cd /path/to/followers_tracker && python main.py >> /path/to/logs/cron.log 2>&1
```

#### Windows (Task Scheduler)
Create a task that runs `python main.py` in the followers_tracker directory daily.

## Testing

To run tests for specific services:

```bash
# Test LinkedIn profile service
python -m tests.unit_tests.test_lkd_profile

# Test Twitter service
python -m tests.unit_tests.test_twitter

# Test Instagram service
python -m tests.unit_tests.test_instagram
```

## Troubleshooting

Common issues and their solutions:

1. **LinkedIn sign-in pages**: If you're consistently hitting sign-in pages, try:
   - Implementing proxy rotation
   - Increasing wait times between requests
   - Using the advanced stealth driver

2. **API rate limits**: For Twitter and YouTube APIs, implement longer wait times between requests.

3. **Missing data**: Check the log files for specific error messages. The application is designed to continue collecting data from other platforms even if one fails.

## Extending the Application

To add support for a new platform, create a new service module in the `services` directory following the established pattern of other services.

## License

This project is proprietary and confidential. Unauthorized copying, distribution, or use is strictly prohibited.