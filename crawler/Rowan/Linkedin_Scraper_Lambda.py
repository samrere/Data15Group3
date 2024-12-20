import asyncio
import pickle
import json
import random
import os
import boto3
from datetime import datetime
import logging
import time
from time import sleep
from linkedin_api import Linkedin
from functools import partial
from typing import Dict, List
import pandas as pd

"""
https://github.com/tomquirk/linkedin-api
"""

# Initialize AWS clients
s3 = boto3.client('s3')

def load_config():
    """Load config from S3"""
    try:
        response = s3.get_object(
            Bucket=os.environ['LINKEDIN_CONFIG_KEY'],  # Add this to Lambda env variables
            Key='linkedin_config.json'  # Your config file name in S3
        )
        return json.loads(response['Body'].read().decode('utf-8'))
    except Exception as e:
        logger.error(f"Error loading config from S3: {str(e)}")
        raise

def custom_evade():
    """Custom method to evade suspension with configurable delay."""
    config = load_config()  # Get latest config
    sleep(random.randint(
        config['sleep_times']['min'],
        config['sleep_times']['max']
    ))

def patched_get_job(self, job_id: str) -> Dict:
    """Fetch data about a given job with configured decoration ID."""
    config = load_config()  # Get latest config
    params = {
        "decorationId": config['api_settings']['job_decoration_id'],
    }
    res = self._fetch(f"/jobs/jobPostings/{job_id}", params=params)
    data = res.json()
    if data and "status" in data and data["status"] != 200:
        self.logger.info("request failed: {}".format(data["message"]))
        return {}
    return data

import linkedin_api.linkedin as linkedin_module
linkedin_module.default_evade = custom_evade
linkedin_module.Linkedin.get_job = patched_get_job

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_workplace_type(workplace_types: List[str]) -> str:
    """Map workplace type URN to readable format"""
    workplace_mapping = {
        'urn:li:fs_workplaceType:1': 'On-site',
        'urn:li:fs_workplaceType:2': 'Remote',
        'urn:li:fs_workplaceType:3': 'Hybrid'
    }
    return workplace_mapping.get(workplace_types[0], "N/A") if workplace_types else "N/A"

def load_cookies(account_key: str) -> Dict:
    """Load cookies from S3"""
    config = load_config()
    account = config['accounts'][account_key]
    cookie_file = account['cookie_file']
    local_path = f"/tmp/{cookie_file}"
    
    s3.download_file(
        os.environ['LINKEDIN_COOKIES_KEY'],
        cookie_file,
        local_path
    )
    
    with open(local_path, "rb") as f:
        return pickle.load(f)

async def async_lambda_handler(event, context):
    """Async Lambda function handler"""
    try:
        # Load config and initialize APIs
        config = load_config()
        
        # Initialize LinkedIn clients
        api1 = Linkedin(config['accounts']['account1']['email'], "", 
                       cookies=load_cookies('account1'))
        logger.info("Account 1 authenticated")
        
        api2 = Linkedin(config['accounts']['account2']['email'], "", 
                       cookies=load_cookies('account2'))
        logger.info("Account 2 authenticated")
        
        api3 = Linkedin(config['accounts']['account3']['email'], "", 
                       cookies=load_cookies('account3'))
        logger.info("Account 3 authenticated")

        async def search_jobs(api: Linkedin, search_params: Dict) -> List[Dict]:
            """Async wrapper for LinkedIn job search"""
            search_func = partial(api.search_jobs, 
                                keywords=search_params['keywords'],
                                location_name=search_params['location_name'],
                                limit=search_params['limit'],
                                listed_at=search_params['listed_at'],
                                offset=search_params['offset'] 
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
                    logger.error("Job ID not found")
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
                listed_at_epoch = job.get('listedAt') or job_details.get('listedAt')


                expire_at = job.get('expireAt') or job_details.get('expireAt')
                expire_time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(expire_at / 1000)) if expire_at else "N/A"
                expire_at_epoch = job.get('expireAt') or job_details.get('expireAt')

                # Extract apply URL
                apply_method = job_details.get("applyMethod", {})
                apply_url = (
                    apply_method.get("com.linkedin.voyager.jobs.ComplexOnsiteApply", {}).get("easyApplyUrl")
                    or apply_method.get("com.linkedin.voyager.jobs.OffsiteApply", {}).get("companyApplyUrl")
                    or "N/A"
                )
                """
                # Extract companyid
                company_id = job_details.get("companyDetails").get('com.linkedin.voyager.deco.jobs.web.shared.WebJobPostingCompany', 
                                                                {}).get('companyResolutionResult', 
                                                                        {}).get('entityUrn', '').split(':')[-1]
                # Extract company_url
                company_url = job_details.get("companyDetails").get('com.linkedin.voyager.deco.jobs.web.shared.WebJobPostingCompany', 
                                                                    {}).get('companyResolutionResult', {}).get('url')
                """

                """
                # store JD into json
                directory_name = f"JD_{config['search_params']['keywords'].replace(' ', '_')}"
                os.makedirs(directory_name, exist_ok=True)

                description = job_details.get('description', {}).get('text', "N/A")
                description_file = os.path.join(directory_name, f"{job_id}.json")

                with open(description_file, 'w') as f:
                    json.dump({"description": description}, f, indent=4)
                """

                # Compile job information
                job_info = {
                    "job_id": job_id,
                    "title": job.get('title', "N/A"),
                    "company": company,
                    "location": location,
                    #"company_id":company_id,
                    #"company_url":company_url,
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
                    "posted_time_epoch": listed_at_epoch,
                    "expire_time": expire_time,
                    "expire_time_epoch": expire_at_epoch,
                    "apply_url": apply_url
                }

                JD_info = {
                    "job_id": job_id,
                    "description": job_details.get('description', {}).get('text', "N/A")
                }

                logger.info(f"Processed job: {job_info['title']} at {job_info['company']}")
                return job_info, JD_info

            except Exception as e:
                logger.error(f"Error processing job {job_id}: {str(e)}")
                return None

        # Main processing
        all_jobs = []
        all_JDs = []
        #all_descriptions = []
        base_params = config['search_params'].copy()
        
        logger.info("Starting job search...")
        
        for page in range(config['api_settings']['number_of_pages']):
            offset = page * config['search_params']['limit']
            base_params['offset'] = offset
            logger.info(f"Searching page {page + 1} (offset {offset})...")
            
            jobs = await search_jobs(api1, base_params)
            logger.info(f"Found {len(jobs)} jobs on page {page + 1}")
            
            for job in jobs:
                result = await process_job(job)
                if result is not None:
                    job_info, JD_info = result
                    all_jobs.append(job_info)
                    all_JDs.append(JD_info)

            if len(jobs) < config['search_params']['limit']:
                logger.info(f"Found {len(jobs)} jobs which is less than limit {config['search_params']['limit']}, stopping search...")
                break

        # Save results to S3
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        jobs_base_key = f"raw/{config['search_params']['keywords'].replace(' ', '_')}/{timestamp}"
        JDs_base_key = f"raw/{config['search_params']['keywords'].replace(' ', '_')}/{timestamp}"
        """
        # Save jobs JSON
        jobs_json = json.dumps(all_jobs, indent=4)
        s3.put_object(
            Bucket=os.environ['LINKEDIN_OUTPUT_KEY'],
            Key=f"{base_key}/jobs.json",
            Body=jobs_json
        )
        """
        # Save jobs parquet
        df_jobs = pd.DataFrame(all_jobs)
        jobs_parquet = df_jobs.to_parquet()
        s3.put_object(
            Bucket=os.environ['LINKEDIN_DATALAKE_KEY'],
            Key=f"{jobs_base_key}/jobs_info.parquet",
            Body=jobs_parquet
        )
        logger.info(f"Job data saved to S3: s3://{os.environ['LINKEDIN_DATALAKE_KEY']}/{jobs_base_key}/")

        # Save descriptions parquet
        df_JDs = pd.DataFrame(all_JDs)
        descriptions_parquet = df_JDs.to_parquet()
        s3.put_object(
            Bucket=os.environ['LINKEDIN_JD_KEY'],
            Key=f"{JDs_base_key}/JDs.parquet",
            Body=descriptions_parquet
        )
        logger.info(f"JD data saved to S3: s3://{os.environ['LINKEDIN_JD_KEY']}/{JDs_base_key}/")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Successfully processed jobs',
                'jobs_processed': len(all_jobs),
                'datalake_path': f"s3://{os.environ['LINKEDIN_DATALAKE_KEY']}/{jobs_base_key}/",
                'JD_path': f"s3://{os.environ['LINKEDIN_JD_KEY']}/{jobs_base_key}/",
            })
        }
        
    except Exception as e:
        logger.error(f"Error in lambda function: {str(e)}")
        raise

def lambda_handler(event, context):
    """Synchronous Lambda function handler"""
    return asyncio.run(async_lambda_handler(event, context))

if __name__ == "__main__":
    lambda_handler(None, None)