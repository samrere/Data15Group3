from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate
from typing import List, Dict
from prompts.templates import ANALYSIS_TEMPLATE


class LLM:
    def __init__(self):
        self.llm = ChatAnthropic(model="claude-3-5-sonnet-latest")

    def generate_response(
        self, user_input: str, resume_text: str, relevant_jobs: List[Dict]
    ) -> str:
        """Generate response using claude.ai"""
        try:
            prompt = ChatPromptTemplate.from_template(ANALYSIS_TEMPLATE)

            messages = prompt.format_messages(
                user_input=user_input,
                resume_text=resume_text,
                relevant_jobs=relevant_jobs,
            )

            response = self.llm.predict_messages(messages)
            return response.content
        except Exception as e:
            raise Exception(f"Error generating response: {str(e)}")
