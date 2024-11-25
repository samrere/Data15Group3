from linkedin_api import Linkedin
import time
import json
import logging
from pprint import pprint

# Setup logging for errors and debugging
logging.basicConfig(filename='job_scraper_errors.log', level=logging.ERROR)

# Authenticate using your LinkedIn credentials
email = ""  # Replace with your LinkedIn email
password = ""  # Replace with your LinkedIn password
api = Linkedin(email, password)

# Test authentication
try:
    profile = api.get_profile()
    print(f"Authenticated as: {profile['firstName']} {profile['lastName']}")
except Exception as e:
    print(f"Authentication failed: {e}")
    exit()

# Define job search parameters
search_params = {
    'keywords': 'data engineer',
    'location_name': 'Sydney',
    'count': 30,  # Results per page
    'limit': 10  # Max results (adjust as needed)
}

# Initialize storage for job data
all_jobs = []

# Fetch jobs
try:
    print("\nSearching for jobs...")
    jobs = api.search_jobs(**search_params)
    print(f"Found {len(jobs)} jobs.")

    # Fetch job details
    for job in jobs:
        try:
            # Extract job ID
            job_id = job.get('id') or job.get('entityUrn', '').split(':')[-1]
            if not job_id:
                print("Job ID not found, skipping...")
                continue

            # Fetch job details
            job_details = api.get_job(job_id)
            job_skills = api.get_job_skills(job_id)

            # Debugging: Print available keys
            print(f"\nJob ID: {job_id}")
            print("-" * 30)
            print(f"Job keys: {list(job.keys())}")
            print(f"Job details keys: {list(job_details.keys())}")
            print(f"Job Skills Data for Job ID {job_id}:")
            pprint(job_skills)

            # Extract relevant fields

            # Company extraction
            company = (
                job.get('companyName') or
                job_details.get('companyName') or
                job_details.get('companyDetails', {}).get('companyName') or
                job_details.get('companyDetails', {}).get('company', {}).get('name') or
                job_skills.get('company', {}).get('name') or
                "N/A"
            )

            # Location extraction
            location = (
                job.get('formattedLocation') or
                job_details.get('formattedLocation') or
                job_details.get('locationDescription') or
                job_details.get('location', {}).get('city') or
                job_details.get('location', {}).get('country') or
                "N/A"
            )

            # Extract skills
            if 'skillMatchStatuses' in job_skills:
                skills = [
                    skill_status.get('skill', {}).get('name', 'Unknown Skill')
                    for skill_status in job_skills.get('skillMatchStatuses', [])
                ]
            else:
                skills = ["Skills not listed"]

            # Extract posting time
            listed_at = job.get('listedAt') or job_details.get('listedAt')
            if listed_at:
                # Convert LinkedIn timestamp to human-readable format
                post_time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(listed_at / 1000))
            else:
                post_time = "N/A"

            # Store job data
            job_info = {
                "title": job.get('title', "N/A"),
                "company": company,
                "location": location,
                "description": job_details.get('description', {}).get('text', "N/A"),
                "skills": skills,
                "job_url": f"https://www.linkedin.com/jobs/view/{job_id}",
                "posted_time": post_time
            }

            print(f"Fetched job: {job_info['title']} at {job_info['company']}")
            all_jobs.append(job_info)

            # Throttle requests
            time.sleep(2)

        except Exception as detail_error:
            logging.error(f"Error fetching details for job ID {job_id}: {detail_error}")
            print(f"Error fetching details for job ID {job_id}: {detail_error}")

except Exception as search_error:
    logging.error(f"Error searching for jobs: {search_error}")
    print(f"Error searching for jobs: {search_error}")

# Save jobs to a JSON file
output_file = "linkedin_jobs.json"
with open(output_file, 'w') as f:
    json.dump(all_jobs, f, indent=4)

print(f"\nJob data saved to {output_file}.")
