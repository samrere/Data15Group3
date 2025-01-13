import json
import boto3
from datetime import datetime
from typing import List
from model.schemas import Job
from core.config import get_settings
from core.exceptions import S3StorageError
import logging


logger = logging.getLogger(__name__)


class JDS3Repository:
    """Repository for managing jd data in s3"""

    def __init__(self):
        self.settings = get_settings()
        self.s3_client = self._initialise_s3_client()

    def _initialise_s3_client(self):
        """Initialise s3 client"""
        try:
            return boto3.client(
                "s3",
                aws_access_key_id=self.settings.aws_access_key_id,
                aws_secret_access_key=self.settings.aws_secret_access_key,
                region_name=self.settings.aws_region,
            )
        except Exception as e:
            raise S3StorageError(f"Failed to initialise s3 client: {str(e)}")

    def _parse_job_data(self, data: dict) -> Job:
        """Parse job data with proper datetime handling"""

        try:
            # Handle URL fields
            if data.get("apply_url") in ["N/A", "", None]:
                data["apply_url"] = None
            if data.get("company_url") in ["N/A", "", None]:
                data["company_url"] = None

            if isinstance(data.get("posted_time"), str):
                data["posted_time"] = datetime.fromisoformat(data["posted_time"])
            if isinstance(data.get("expire_time"), str):
                data["expire_time"] = datetime.fromisoformat(data["expire_time"])

            return Job(**data)
        except Exception as e:
            logger.error(f"Error parsing job data: {str(e)}")
            logger.debug(f"Problematic data: {type(data)}: {data}")
            raise S3StorageError(f"Failed to parse job data: {str(e)}")

    async def load_jobs(self) -> List[Job]:
        """Load jobs from s3"""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.settings.aws_s3_jd_bucket,
                Prefix=self.settings.aws_s3_jobs_path,
            )

            all_jobs = []
            for obj in response.get("Contents", []):
                if obj["Key"].endswith(".json"):
                    jobs_data = await self._load_job_file(obj["Key"])
                    parsed_jobs = [self._parse_job_data(job) for job in jobs_data]
                    all_jobs.extend(parsed_jobs)

            return all_jobs
        except Exception as e:
            raise S3StorageError(f"Failed to load jobs from s3: {str(e)}")

    async def load_dev_job(self) -> Job:
        """Test run"""
        try:
            jobs_data = await self._load_job_file(self.settings.aws_s3_dev_jd_file)
            # Get the first job from the file
            if jobs_data and len(jobs_data) > 0:
                all_jobs = []
                all_jobs.extend([self._parse_job_data(job) for job in jobs_data])
                return all_jobs
            else:
                raise S3StorageError("No jobs found in test file")

        except Exception as e:
            raise S3StorageError(f"Failed to load dev job: {str(e)}")

    async def _load_job_file(self, key: str) -> List[dict]:
        """Load and parse single job file"""
        try:
            file_obj = self.s3_client.get_object(
                Bucket=self.settings.aws_s3_jd_bucket, Key=key
            )
            content = file_obj["Body"].read()
            return json.loads(content)
        except Exception as e:
            raise S3StorageError(f"Failed to load job file {key}: {str(e)}")
