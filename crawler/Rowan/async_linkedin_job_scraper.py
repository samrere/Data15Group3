import asyncio
import pickle
import json
import random
import os
from datetime import datetime
import logging
import time
from time import sleep
from linkedin_api import Linkedin
from functools import partial
from typing import Dict, List

# Load config
def load_config():
    with open('config.json', 'r') as f:
        return json.load(f)

config = load_config()


#Patch LinkedIn API functions
def custom_evade():
    """Custom method to evade suspension with configurable delay."""
    sleep(random.randint(
        config['sleep_times']['min'],
        config['sleep_times']['max']
    ))

def patched_get_job(self, job_id: str) -> Dict:
    """Fetch data about a given job with configured decoration ID."""
    params = {
        "decorationId": config['api_settings']['job_decoration_id'],
    }
    res = self._fetch(f"/jobs/jobPostings/{job_id}", params=params)
    data = res.json()
    if data and "status" in data and data["status"] != 200:
        self.logger.info("request failed: {}".format(data["message"]))
        return {}
    return data

# Apply patches
import linkedin_api.linkedin as linkedin_module
linkedin_module.default_evade = custom_evade
linkedin_module.Linkedin.get_job = patched_get_job



# Setup logging for errors and debugging
logging.basicConfig(filename='job_scraper_errors.log', level=logging.ERROR)

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

def get_workplace_type(workplace_types: List[str]) -> str:
    """Map workplace type URN to readable format"""
    workplace_mapping = {
        'urn:li:fs_workplaceType:1': 'On-site',
        'urn:li:fs_workplaceType:2': 'Remote',
        'urn:li:fs_workplaceType:3': 'Hybrid'
    }
    return workplace_mapping.get(workplace_types[0], "N/A") if workplace_types else "N/A"

def load_cookies(email: str) -> Dict:
    """Load cookies from file for authentication"""
    cookies_file = f"{email}.jr"
    with open(cookies_file, "rb") as f:
        return pickle.load(f)

# authenticate api

api1 = Linkedin(config['accounts']['account1']['email'], 
                "", 
                cookies=load_cookies(config['accounts']['account1']['email'])
                )
print("Account 1 authenticated")

api2 = Linkedin(config['accounts']['account2']['email'], 
                "", 
                cookies=load_cookies(config['accounts']['account2']['email'])
                )
print("Account 2 authenticated")

api3 = Linkedin(config['accounts']['account3']['email'], 
                "", 
                cookies=load_cookies(config['accounts']['account3']['email'])
                )
print("Account 3 authenticated")

async def search_jobs(api: Linkedin, search_params: Dict) -> List[Dict]:
    """Async wrapper for LinkedIn job search"""
    search_func = partial(api.search_jobs, 
                         keywords=search_params['keywords'],
                         location_name=search_params['location_name'],
                         limit=search_params['limit'],
                         listed_at=search_params['listed_at']
                         #offset=search_params['offset'] 
                         )
    return await asyncio.get_event_loop().run_in_executor(None, search_func)

async def get_job_details(api: Linkedin, job_id: str) -> Dict:
    """Async wrapper for getting job details"""
    return await asyncio.get_event_loop().run_in_executor(
        None, api.get_job, job_id
    )

async def get_job_skills(api: Linkedin, job_id: str) -> Dict:
    """Async wrapper for getting job skills"""
    return await asyncio.get_event_loop().run_in_executor(
        None, api.get_job_skills, job_id
    )

async def process_job(job: Dict) -> Dict:
    """Process a single job using parallel API calls"""
    try:
        job_id = job.get('id') or job.get('entityUrn', '').split(':')[-1]
        if not job_id:
            logging.error("Job ID not found")
            return None

        # Run job details and skills API calls in parallel using different accounts
        job_details_task = get_job_details(api2, job_id)
        job_skills_task = get_job_skills(api3, job_id)
        
        # Wait for both API calls to complete
        job_details, job_skills = await asyncio.gather(job_details_task, job_skills_task)

        # Extract company information
        company = (
            job.get('companyName') or
            job_details.get('companyName') or
            job_details.get('companyDetails', {}).get('companyName') or
            job_details.get('companyDetails', {}).get('company', {}).get('name') or
            job_skills.get('company', {}).get('name') or
            "N/A"
        )

        # Extract location
        location = (
            job.get('formattedLocation') or
            job_details.get('formattedLocation') or
            job_details.get('locationDescription') or
            job_details.get('location', {}).get('city') or
            "N/A"
        )

        # Extract skills
        skills = [
            skill_status.get('skill', {}).get('name', 'Unknown Skill')
            for skill_status in job_skills.get('skillMatchStatuses', [])
        ] if 'skillMatchStatuses' in job_skills else ["Skills not listed"]

        # Process timestamps
        listed_at = job.get('listedAt') or job_details.get('listedAt')
        post_time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(listed_at / 1000)) if listed_at else "N/A"
        
        expire_at = job.get('expireAt') or job_details.get('expireAt')
        expire_time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(expire_at / 1000)) if expire_at else "N/A"

        # Extract apply URL
        apply_method = job_details.get("applyMethod", {})
        apply_url = (
            apply_method.get("com.linkedin.voyager.jobs.ComplexOnsiteApply", {}).get("easyApplyUrl")
            or apply_method.get("com.linkedin.voyager.jobs.OffsiteApply", {}).get("companyApplyUrl")
            or "N/A"
        )

        # Extract companyid
        company_id = job_details.get("companyDetails").get('com.linkedin.voyager.deco.jobs.web.shared.WebJobPostingCompany', 
                                                           {}).get('companyResolutionResult', 
                                                                   {}).get('entityUrn', '').split(':')[-1]
        # Extract company_url
        company_url = job_details.get("companyDetails").get('com.linkedin.voyager.deco.jobs.web.shared.WebJobPostingCompany', 
                                                            {}).get('companyResolutionResult', {}).get('url')
        
        # store JD into json
        """
        description = job_details.get('description', {}).get('text', "N/A")
        description_file = os.path.join("JD_test", f"{job_id}.json")
        with open(description_file, 'w') as f:
            json.dump({"description": description}, f, indent=4)
        """
        # Compile job information
        job_info = {
            "title": job.get('title', "N/A"),
            "company": company,
            "location": location,
            "company_id":company_id,
            "company_url":company_url,
            "employment_type": job_details.get('formattedEmploymentStatus', "N/A"),
            "seniority_level": job_details.get('formattedExperienceLevel', "N/A"),
            "industries": job_details.get('formattedIndustries', "N/A"),
            "job_functions": job_details.get('formattedJobFunctions', "N/A"),
            "applies": job_details.get('applies', "N/A"),
            "workplace_type": get_workplace_type(job_details.get('workplaceTypes', [])),
            #"description": job_details.get('description', {}).get('text', "N/A"),
            "skills": skills,
            "job_url": f"https://www.linkedin.com/jobs/view/{job_id}",
            "reposted": job.get('repostedJob', "N/A"),
            "posted_time": post_time,
            "expire_time": expire_time,
            "apply_url": apply_url
        }

        print(f"Processed job: {job_info['title']} at {job_info['company']}")
        return job_info

    except Exception as e:
        logging.error(f"Error processing job {job_id}: {str(e)}")
        return None

async def main():
    """Main function to orchestrate job scraping"""

    try:

        all_jobs = []
        
        # Get initial job listings using first account
        print("\nSearching for jobs...")



        jobs = await search_jobs(api1, config['search_params'])
        print(f"Found {len(jobs)} jobs")
        
        
        for job in jobs:
            result = await process_job(job)
            if result is not None:
                all_jobs.append(result)
        
        # Save to JSON file

        output_file = f"linkedin_jobs_{config['search_params']['keywords'].replace(' ', '_')}_{timestamp}.json"
        with open(output_file, 'w') as f:
            json.dump(all_jobs, f, indent=4)
        
        print(f"\nJob data saved to {output_file}.")
        
    except Exception as e:
        logging.error(f"Error in main function: {str(e)}")
        print(f"Error occurred: {str(e)}")

if __name__ == "__main__":
    start_time = time.time()
    asyncio.run(main())
    end_time = time.time()
    print(f"\nTotal execution time: {end_time - start_time:.2f} seconds")