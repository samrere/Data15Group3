from typing import List
from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate
from langchain.schema.messages import HumanMessage
from model.schemas import VectorSearchResult
from prompts.template import ANALYSIS_PROMPT
from core.config import get_settings


class LLM:
    """LLM used to for generating responses"""

    def __init__(self):
        settings = get_settings()
        self.llm = ChatAnthropic(
            api_key=settings.anthropic_api_key,
            model=settings.anthropic_chat_model,
            temperature=0.1,
        )
        self.prompt = ChatPromptTemplate.from_template(ANALYSIS_PROMPT)

    async def generate_response(
        self, question: str, resume_text: str, relevant_jobs: List[VectorSearchResult]
    ) -> str:
        """Generate response using Claude"""
        prompt_value = self.prompt.format_messages(
            question=question,
            resume_text=resume_text,
            relevant_jobs="\n".join(
                f"- {result.job.title} at {result.job.company} (Match Score: {result.score:.2f})"
                for result in relevant_jobs
            ),
        )

        message = HumanMessage(content=prompt_value)
        response = await self.llm.astream(input=message)
        return response.content
