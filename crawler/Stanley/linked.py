from linkedin_api import Linkedin  # Main library to interact with LinkedIn
import time  # For adding delays between requests
import json  # For saving data in JSON format
import pandas as pd  # For handling data and saving to CSV
from datetime import datetime  # For timestamps
import logging  # For keeping track of what the script is doing
from typing import List, Dict  # For type hints (making code clearer)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LinkedInJobScraper:
    def __init__(self, email: str, password: str, delay: int = 5):
        """
        Initialize the LinkedIn Job Scraper
        
        Args:
            email: LinkedIn login email
            password: LinkedIn login password
            delay: Delay between requests in seconds
        """
        self.delay = delay
        self.api = self._initialize_linkedin_api(email, password)
        
    def _initialize_linkedin_api(self, email: str, password: str, max_retries: int = 3) -> Linkedin:
        """Initialize LinkedIn API with retry logic"""
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempt {attempt + 1} to authenticate...")
                api = Linkedin(email, password)
                logger.info("Authentication successful!")
                return api
            except Exception as e:
                logger.error(f"Authentication failed: {str(e)}")
                if attempt < max_retries - 1:
                    logger.info("Waiting 60 seconds before retrying...")
                    time.sleep(60)
                else:
                    raise
    
    def _extract_job_details(self, job_data: Dict) -> Dict:
        """Extract relevant job details from API response"""
        try:
            # Extract basic job information
            job_details = {
                'job_id': job_data.get('entityUrn', '').split(':')[-1],
                'job_title': job_data.get('title', ''),
                'company_name': job_data.get('companyName', ''),
                'location': job_data.get('formattedLocation', ''),
                'listed_time': job_data.get('listedAt', ''),
                'employment_type': job_data.get('employmentStatus', ''),
                'seniority_level': job_data.get('experience', ''),
                'job_description': job_data.get('description', {}).get('text', ''),
                'applies': job_data.get('applies', 0),
                'remote_allowed': job_data.get('workRemoteAllowed', False),
            }
            
            # Extract salary information if available
            salary_info = job_data.get('salaryInsights', {})
            if salary_info:
                job_details.update({
                    'salary_min': salary_info.get('salaryMin', ''),
                    'salary_max': salary_info.get('salaryMax', ''),
                    'salary_currency': salary_info.get('salaryCurrency', ''),
                    'salary_period': salary_info.get('salaryPeriod', '')
                })
            
            # Extract required skills if available
            skills = job_data.get('requiredSkills', [])
            job_details['required_skills'] = ', '.join(skills) if skills else ''
            
            # Add scraping timestamp
            job_details['scrape_timestamp'] = datetime.now().isoformat()
            
            return job_details
            
        except Exception as e:
            logger.error(f"Error extracting job details: {str(e)}")
            return {}

    def search_jobs(self, 
                   keywords: str,
                   location_name: str,
                   limit: int = 100,
                   offset: int = 0) -> List[Dict]:
        """
        Search for jobs and get detailed information
        
        Args:
            keywords: Job search keywords
            location_name: Location to search in
            limit: Maximum number of jobs to fetch
            offset: Starting point for search results
        """
        try:
            logger.info(f"Searching for {keywords} jobs in {location_name}")
            
            # Get initial job listings
            jobs = self.api.search_jobs(
                keywords=keywords,
                location_name=location_name,
                limit=limit,
                offset=offset
            )
            
            detailed_jobs = []
            for idx, job in enumerate(jobs, 1):
                try:
                    job_id = job['entityUrn'].split(':')[-1]
                    logger.info(f"Fetching details for job {idx}/{len(jobs)} (ID: {job_id})")
                    
                    # Get detailed job information
                    job_details = self.api.get_job(job_id)
                    
                    # Extract relevant information
                    processed_job = self._extract_job_details(job_details)
                    if processed_job:
                        detailed_jobs.append(processed_job)
                    
                    # Add delay between requests
                    time.sleep(self.delay)
                    
                except Exception as e:
                    logger.error(f"Error processing job {job_id}: {str(e)}")
                    continue
            
            return detailed_jobs
            
        except Exception as e:
            logger.error(f"Error in search_jobs: {str(e)}")
            return []
    
    def save_results(self, jobs: List[Dict], 
                    csv_file: str = None, 
                    json_file: str = None):
        """Save job results to CSV and/or JSON files"""
        if not jobs:
            logger.warning("No jobs to save")
            return
        
        # Save to CSV
        if csv_file:
            try:
                df = pd.DataFrame(jobs)
                df.to_csv(csv_file, index=False)
                logger.info(f"Saved {len(jobs)} jobs to {csv_file}")
            except Exception as e:
                logger.error(f"Error saving CSV file: {str(e)}")
        
        # Save to JSON
        if json_file:
            try:
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(jobs, f, indent=2, ensure_ascii=False)
                logger.info(f"Saved {len(jobs)} jobs to {json_file}")
            except Exception as e:
                logger.error(f"Error saving JSON file: {str(e)}")

def main():
    # Configuration
    EMAIL = '' # replace with your actual account
    PASSWORD = '' # replace with actual password
    
    # Initialize scraper
    scraper = LinkedInJobScraper(EMAIL, PASSWORD, delay=5)
    
    # Define search parameters
    search_params = [
        {
            'keywords': 'Data Enginner',
            'location_name': 'Australia',
            'limit': 30
        },
        # Add more search configurations as needed
    ]
    
    # Run searches
    for params in search_params:
        try:
            # Search for jobs
            jobs = scraper.search_jobs(**params)
            
            if jobs:
                # Generate filenames with timestamp
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                base_filename = f"linkedin_jobs_{params['keywords'].replace(' ', '_')}_{timestamp}"
                
                # Save results
                scraper.save_results(
                    jobs,
                    csv_file=f"{base_filename}.csv",
                    json_file=f"{base_filename}.json"
                )
            
            # Add delay between searches
            time.sleep(10)
            
        except Exception as e:
            logger.error(f"Error processing search {params}: {str(e)}")
            continue

if __name__ == "__main__":
    main()