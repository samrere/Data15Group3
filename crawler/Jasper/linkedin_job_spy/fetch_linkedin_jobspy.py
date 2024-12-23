from jobspy import scrape_jobs
import time
import pandas as pd
import json
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ScraperConfig:
    """Configuration class to hold all adjustable parameters"""
    # Search parameters
    search_term: str
    location: str
    distance: int
    is_remote: bool

    # Batch control
    batch_size: int
    total_wanted: int

    # Timing parameters
    base_delay: int
    retry_delay: int
    max_retries: int

    # Data collection settings
    fetch_description: bool
    enforce_annual_salary: bool
    description_format: str
    verbose_level: int


class LinkedInJobScraper:
    """
    A comprehensive LinkedIn job scraper with rate limiting handling and data processing.
    """

    def __init__(self, config: ScraperConfig):
        """Initialize scraper with configurable parameters"""
        self.config = config
        self.search_params = {
            "site_name": ["linkedin"],
            "search_term": config.search_term,
            "location": config.location,
            "distance": config.distance,
            "is_remote": config.is_remote,
            "linkedin_fetch_description": config.fetch_description,
            "enforce_annual_salary": config.enforce_annual_salary,
            "description_format": config.description_format,
            "verbose": config.verbose_level
        }

    def search_batch_with_retry(self, offset: int, retry_count: int = 0) -> Tuple[pd.DataFrame, bool]:
        """
        Attempts to fetch a batch of jobs with retry logic for rate limiting.

        Args:
            offset: Starting position for the job search
            retry_count: Number of retry attempts made so far

        Returns:
            Tuple of (DataFrame of jobs, boolean indicating if rate limited)
        """
        try:
            batch = scrape_jobs(
                **self.search_params,
                results_wanted=self.config.batch_size,
                offset=offset
            )
            return batch, False

        except Exception as e:
            error_str = str(e).lower()

            if '429' in error_str or 'too many' in error_str:
                print("retry ing ... please wait ;)")
                if retry_count < self.config.max_retries:
                    wait_time = self.config.retry_delay * (retry_count + 1)
                    print(
                        f"\nRate limit detected at offset {offset}. Attempt {retry_count + 1}/{self.config.max_retries}")
                    print(f"Waiting {wait_time} seconds before retrying...")
                    time.sleep(wait_time)
                    return self.search_batch_with_retry(offset, retry_count + 1)
                else:
                    print(f"\nMax retries ({self.config.max_retries}) reached at offset {offset}")
                    return pd.DataFrame(), True
            else:
                print(f"Non-rate-limit error at offset {offset}: {e}")
                return pd.DataFrame(), False

    def parse_location(self, location_str: str) -> Dict[str, str]:
        """
        Parse location string into components.
        Example: 'Sydney, New South Wales, Australia' ->
                {'city': 'Sydney', 'state': 'New South Wales', 'country': 'Australia'}
        """
        if not location_str or location_str == 'Not specified':
            return {
                'raw_location': location_str,
                'city': None,
                'state': None,
                'country': None
            }

        parts = [part.strip() for part in location_str.split(',')]
        location_data = {
            'raw_location': location_str,
            'city': parts[0] if len(parts) > 0 else None,
            'state': parts[1] if len(parts) > 1 else None,
            'country': parts[2] if len(parts) > 2 else None
        }
        return location_data

    def process_job_data(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Transforms raw job data into a structured format with enhanced information.
        Organizes data into logical categories and adds metadata.

        Args:
            df: DataFrame containing raw job data

        Returns:
            List of dictionaries containing processed job data
        """
        processed_jobs = []

        for _, job in df.iterrows():
            processed_job = {
                "basic_info": {
                    "title": job.get('title'),
                    "company": job.get('company'),
                    "company_url": job.get('company_url'),
                    "job_url": job.get('job_url'),
                    "date_posted": str(job.get('date_posted'))
                },
                "location": self.parse_location(job.get('location', 'Not specified')),
                "compensation": {
                    "interval": job.get('interval'),
                    "min_amount": job.get('min_amount'),
                    "max_amount": job.get('max_amount'),
                    "currency": job.get('currency')
                },
                "job_details": {
                    "description": job.get('description'),
                    "job_type": job.get('job_type'),
                    "job_function": job.get('job_function'),
                    "job_level": job.get('job_level')
                },
                "company_details": {
                    "industry": job.get('company_industry'),
                    "employees": job.get('company_employees_label'),
                    "revenue": job.get('company_revenue_label'),
                    "description": job.get('company_description')
                },
                "metadata": {
                    "scraped_at": datetime.now().isoformat(),
                    "source": "linkedin",
                    "batch_id": str(time.time())
                }
            }
            processed_jobs.append(processed_job)

        return processed_jobs

    def save_to_json(self, jobs: List[Dict], filename: str = None) -> str:
        """
        Saves the collected job data to a structured JSON file with metadata.

        Args:
            jobs: List of processed job dictionaries
            filename: Optional custom filename

        Returns:
            Path to saved JSON file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"linkedin_jobs_{timestamp}.json"

        output_data = {
            "metadata": {
                "search_timestamp": datetime.now().isoformat(),
                "search_parameters": self.search_params,
                "total_jobs_found": len(jobs),
                "search_location": self.config.location,
                "job_type": self.config.search_term
            },
            "jobs": jobs
        }

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            print(f"Successfully saved detailed job data to {filename}")
            return filename
        except Exception as e:
            print(f"Error saving JSON: {e}")
            return None

    def execute_search(self) -> str:
        """
        Executes the complete search with error handling and retry logic.
        Manages the entire scraping process including pagination and rate limiting.

        Returns:
            Path to saved JSON file containing all collected jobs
        """
        all_jobs = []
        start_time = time.time()
        previous_total = 0

        for offset in range(0, self.config.total_wanted, self.config.batch_size):
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n[{current_time}] Fetching batch: jobs {offset + 1}-{offset + self.config.batch_size}")

            # Try to fetch this batch with retries
            batch_jobs, was_rate_limited = self.search_batch_with_retry(offset)

            if was_rate_limited:
                print(f"\nSaving progress: {len(all_jobs)} jobs collected before rate limit")
                break

            if batch_jobs.empty:
                if offset == 0:
                    print("No jobs found in initial batch. Check search parameters.")
                    break
                print("\nNo more jobs available. Search complete.")
                break

            processed_batch = self.process_job_data(batch_jobs)
            all_jobs.extend(processed_batch)

            current_total = len(all_jobs)
            new_jobs_found = current_total - previous_total

            print(f"Batch complete:")
            print(f"- New jobs in this batch: {new_jobs_found}")
            print(f"- Total unique jobs: {current_total}")
            print(f"- Current offset: {offset}")
            print(f"- Runtime: {(time.time() - start_time):.1f} seconds")

            if len(batch_jobs) < self.config.batch_size:
                print("\nReached end of available jobs.")
                break

            previous_total = current_total
            print(f"Waiting {self.config.base_delay} seconds...")
            time.sleep(self.config.base_delay)

        return self.save_to_json(all_jobs)


def main():
    """
    Main function with all adjustable parameters.
    Modify these values to customize the scraping behavior.
    """

    # Create a configuration with your desired parameters
    config = ScraperConfig(
        # Search criteria
        search_term="data engineer",  # Job title to search for
        location="Australia",  # Location to search in
        distance=100,  # Search radius in miles
        is_remote=False,  # Include remote jobs

        # Batch and pagination control
        batch_size=20,  # How many jobs to fetch per request
        total_wanted=1000,  # Maximum total jobs to collect

        # Timing controls
        base_delay=25,  # Seconds to wait between normal requests
        retry_delay=48,  # Base seconds to wait after rate limit
        max_retries=3,  # Maximum retry attempts per batch

        # Data collection options
        fetch_description=True,  # Get full job descriptions
        enforce_annual_salary=True,  # Standardize salary to annual
        description_format="markdown",  # Format for job descriptions
        verbose_level=2  # Log level (0=quiet, 1=normal, 2=detailed)
    )

    # Initialize and run the scraper with the configuration
    print("\nStarting LinkedIn Data Engineer Job Search")
    print("Current configuration:")
    print(f"- Searching for: {config.search_term}")
    print(f"- Location: {config.location} (within {config.distance} miles)")
    print(f"- Batch size: {config.batch_size}")
    print(f"- Maximum jobs: {config.total_wanted}")

    scraper = LinkedInJobScraper(config)
    output_file = scraper.execute_search()

    if output_file:
        print("\nSearch Complete!")
        print(f"Job data saved to: {output_file}")


if __name__ == "__main__":
    main()