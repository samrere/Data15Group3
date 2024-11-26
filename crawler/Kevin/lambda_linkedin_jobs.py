import pprint
import time
import logging
import json
from decouple import config
from linkedin_api import Linkedin
from typing import Dict, List, Optional

# Set up logging for AWS
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def setup_linkedin_client() -> Optional[Linkedin]:
    """
    Initialise LinkedIn client with credentials.
    Returns:
        Optional[Linkedin]: Linkedin object
    """
    try:
        return Linkedin(
            username=config("LINKEDIN_USERNAME"), password=config("LINKEDIN_PASSWORD")
        )
    except Exception as e:
        logger.error(f"Failed to initialise LinkedIn client: {str(e)}")
        return None


def parse_job_detail(job_detail: Dict) -> Dict:
    """
    Parse job details from LinkedIn response.
    Args:
        job_detail: Raw job detail dictionary from LinkedIn API
    Returns:
        Dictionary containing parsed job information
    """
    try:
        # Get workplace type safely
        workplace_types = job_detail.get("workplaceTypes", [])
        workplace_type_urn = workplace_types[0] if workplace_types else ""

        return {
            "job_title": job_detail.get("title", "N/A"),
            "company": job_detail.get("companyDetails", {})
            .get(
                "com.linkedin.voyager.deco.jobs.web.shared.WebCompactJobPostingCompany",
                {},
            )
            .get("companyResolutionResult", {})
            .get("name", "N/A"),
            "job_location": job_detail.get("formattedLocation", "N/A"),
            "posted_at": time.ctime(job_detail.get("listedAt", 0) / 1000) or "N/A",
            "job_remote": (
                job_detail.get("workplaceTypesResolutionResults", {})
                .get(workplace_type_urn, {})
                .get(
                    "localizedName",
                    (
                        "On-site"
                        if not job_detail.get("workRemoteAllowed")
                        else "Hybrid/Remote"
                    ),
                )
            ),
            "job_description": job_detail.get("description", {}).get("text", "N/A"),
        }
    except Exception as e:
        logger.error(f"Error parsing job detail: {str(e)}")
        return {}


def get_job_skills(linkedin: Linkedin, job_id: str) -> List[str]:
    """
    Get skills for a specific job.
    Args:
        linkedin: LinkedIn client instance
        job_id: Job ID to fetch skills for
    Returns:
        List of skill names
    """
    try:
        job_skills = linkedin.get_job_skills(job_id)
        if job_skills and "skillMatchStatuses" in job_skills:
            return [
                skill_status.get("skill", {}).get("name", "N/A")
                for skill_status in job_skills.get("skillMatchStatuses", [])
            ]
    except Exception as e:
        logger.error(f"Error fetching skills for job {job_id}: {str(e)}")
    return ["Skills not listed"]


def process_single_job(linkedin: Linkedin, job: Dict) -> Optional[Dict]:
    """
    Process a single job posting.
    Args:
        linkedin: LinkedIn client instance
        job: Job dictionary from search results
    Returns:
        Processed job details or None if processing fails
    """
    try:
        job_id = job.get("entityUrn", "").split(":")[-1]
        logger.info(f"Processing job ID: {job_id}")

        job_detail = linkedin.get_job(job_id)
        if not job_detail:
            logger.warning(f"No details found for job ID: {job_id}")
            return None

        parsed_detail = parse_job_detail(job_detail)
        if not parsed_detail:
            return None

        # Add skills and URL
        parsed_detail.update(
            {
                "job_skills": get_job_skills(linkedin, job_id),
                "job_url": f"https://www.linkedin.com/jobs/view/{job_id}",
            }
        )

        return parsed_detail

    except Exception as e:
        logger.error(f"Error processing job ID {job_id}: {str(e)}")
        return None


def lambda_handler(event, context):
    """
    AWS Lambda handler function.
    """
    try:
        # Initialise LinkedIn client
        linkedin = setup_linkedin_client()
        logger.info("Linkedin crawler initialised")
        if not linkedin:
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "Failed to initialize LinkedIn client"}),
            }

        # Get search parameters from event or use defaults
        keywords = event.get("keywords", "Data Engineer")
        location = event.get("location", "Australia")
        limit = event.get("limit", 5)

        logger.info(
            f"Searching jobs with keywords: {keywords}, location: {location}, limit: {limit}"
        )

        # Search jobs
        jobs = linkedin.search_jobs(
            keywords=keywords, location_name=location, limit=limit
        )

        # Process jobs with delay between requests
        processed_jobs = []
        for job in jobs:
            time.sleep(5)
            if processed_job := process_single_job(linkedin, job):
                processed_jobs.append(processed_job)

        # Return results
        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "jobs_found": len(jobs),
                    "jobs_processed": len(processed_jobs),
                    "results": processed_jobs,
                }
            ),
        }

    except Exception as e:
        logger.error(f"Lambda execution error: {str(e)}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}


# For local testing
# if __name__ == "__main__":
# Simulate Lambda event
# test_event = {"keywords": "Data Engineer", "location": "Australia", "limit": 5}
# result = lambda_handler(test_event, None)
# pprint.pprint(json.loads(result["body"]))
