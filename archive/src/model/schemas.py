from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from datetime import datetime


class Job(BaseModel):
    """Job model"""

    title: str
    company: str
    location: str
    company_id: str
    company_url: Optional[HttpUrl] = None
    employment_type: str
    seniority_level: str = ""
    industries: List[str]
    job_functions: List[str]
    applies: Optional[int] = None
    workplace_type: str
    description: str
    skills: List[str]
    job_url: HttpUrl
    reposted: bool
    posted_time: datetime
    expire_time: datetime
    apply_url: Optional[HttpUrl] = None

    @property
    def job_id(self) -> str:
        """Extract job ID from job URL"""
        return str(self.job_url).split("/")[-1]


class VectorSearchResult(BaseModel):
    """Vector search result model"""

    job: Job
    score: float
