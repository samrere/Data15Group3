from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from typing import List, Dict
import os


class Embedding:
    def __init__(self):
        self.embedding = OpenAIEmbeddings(model="text-embedding-3-large")
        self.vectorstore = self._initialise_vectorstore()

    def _initialise_vectorstore(self) -> Chroma:
        """Initialise Chroma vector store"""
        # TODO: load job descriptions here

        return Chroma(
            collection_name="job_posts",
            embedding_function=self.embedding,
            persist_directory="data/chromadb",
        )

    def get_relevant_jobs(self, resume_text: str, k: int = 5) -> List[Dict]:
        """Get 5 most relevant job posts"""
        try:
            results = self.vectorstore.similarity_search_with_relevance_scores(
                query=resume_text, k=k
            )
            return [{"job": doc.page_content, "score": score} for doc, score in results]
        except Exception as e:
            raise Exception(f"Error retrieving relevant jobs: {str(e)}")
