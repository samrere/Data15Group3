from typing import List, Optional
import json
import boto3
import pinecone
import asyncio
import time
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document
from core.config import get_settings
from core.exceptions import VectorStoreError
from model.schemas import Job, VectorSearchResult
from repositories.s3 import JDS3Repository
import logging


logger = logging.getLogger(__name__)


class VectorStoreRepository:
    """Repository for managing vector store operations"""

    def __init__(self):
        self.settings = get_settings()
        self.embeddings = OpenAIEmbeddings(
            api_key=self.settings.openai_api_key,
            model=self.settings.openai_embedding_model,
            dimensions=self.settings.embedding_dimension,
        )
        self.s3 = JDS3Repository()
        self.vectorstore = None

    @classmethod
    async def create(cls) -> "VectorStoreRepository":
        """Factory method to create and initialise the repository"""
        instance = cls()
        await instance.initialise()
        return instance

    async def initialise(self) -> None:
        """Initialise vector store"""
        if self.vectorstore is not None:
            return

        try:
            # Check pinecone index
            pc = pinecone.Pinecone(api_key=self.settings.pinecone_api_key)
            index_name = self.settings.pinecone_index_name
            existing_indexes = [index_info["name"] for index_info in pc.list_indexes()]

            # If not exists, initialise index from documents
            if index_name not in existing_indexes:
                logger.info(f"Creating new index: {index_name}")
                pc.create_index(
                    name=index_name,
                    dimension=self.settings.embedding_dimension,
                    metric="cosine",
                    spec=pinecone.ServerlessSpec(cloud="aws", region="us-east-1"),
                )
                while not pc.describe_index(index_name).status["ready"]:
                    time.sleep(1)

                # Load jobs from s3
                logger.info("Loading jobs from s3")
                jobs = await self.s3.load_jobs()

                if not jobs:
                    logger.warning("No initial jobs found in S3, creat empty index ...")
                    self.vectorstore = PineconeVectorStore(
                        pinecone_api_key=self.settings.pinecone_api_key,
                        index_name=index_name,
                        embedding=self.embeddings,
                    )
                    return

                # Convert json to documents
                documents = self._jobs_to_documents(jobs=jobs)
                jobs_ids = [job.job_id for job in jobs]

                logger.info(f"Initialising vector store with {len(documents)} jobs")
                self.vectorstore = PineconeVectorStore.from_documents(
                    pinecone_api_key=self.settings.pinecone_api_key,
                    documents=documents,
                    embedding=self.embeddings,
                    index=index_name,
                    ids=jobs_ids,
                )
            else:
                logger.info(f"Connecting to existing index")
                self.vectorstore = PineconeVectorStore(
                    pinecone_api_key=self.settings.pinecone_api_key,
                    index=index_name,
                    embedding=self.embeddings,
                )
        except Exception as e:
            logger.error(f"Error initialising vector store {str(e)}")
            raise VectorStoreError(str(e))

    def _jobs_to_documents(self, jobs: List[Job]) -> List[Document]:
        """Convert jobs to Langchain documents"""
        return [
            Document(
                page_content=job.description,
                metadata={
                    "job_id": job.job_id,
                    "title": job.title,
                    "company": job.company,
                    "location": job.location,
                    "skills": job.skills,
                    "job_url": str(job.job_url),
                    "employment_type": job.employment_type,
                    "industries": job.industries,
                    "job_functions": job.job_functions,
                },
            )
            for job in jobs
        ]

    async def search(self, query: str, k: int = 3) -> List[VectorSearchResult]:
        """Search for relevant jobs"""
        if self.vectorstore is None:
            raise VectorStoreError("Vector store not initialized")

        try:
            results = self.vectorstore.similarity_search_with_score(query=query, k=k)

            return [
                VectorSearchResult(
                    job=Job(
                        title=doc.metadata["title"],
                        company=doc.metadata["company"],
                        location=doc.metadata["location"],
                        description=doc.page_content,
                        employment_type=doc.metadata["employment_type"],
                        industries=doc.metadata["industries"],
                        job_functions=doc.metadata["job_functions"],
                        skills=doc.metadata["skills"],
                        job_url=doc.metadata["job_url"],
                    ),
                    score=score,
                )
                for doc, score in results
            ]
        except Exception as e:
            raise VectorStoreError(f"Failed to search vector store: {str(e)}")
