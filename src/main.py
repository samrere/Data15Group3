import streamlit as st
import asyncio
import tempfile
import os
from typing import Optional
from repositories.vectorstore import VectorStoreRepository
from llm.llm import LLM
from core.exceptions import JobsAIException
from pypdf import PdfReader
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Application:
    """Main app"""

    def __init__(self):
        self.vectorstore = None
        self.llm = None
        self.initialise_session_state()

    def initialise_session_state(self):
        """Initialise session state variable"""
        if "messages" not in st.session_state:
            st.session_state.messages = [
                {
                    "role": "assistant",
                    "content": "Hey there! I'm your personal career coach. What position are you looking for? Please upload your resume & type the role you're interested in the chat input window and hit enter to start! ",
                }
            ]
        if "resume_uploaded" not in st.session_state:
            st.session_state.resume_uploaded = False
        if "resume_text" not in st.session_state:
            st.session_state.resume_text = None

    async def initialise(self):
        """Initialize application services"""
        try:
            self.vector_store = await VectorStoreRepository.create()
            self.llm_service = LLM()
            logger.info("Application initialised successfully")
        except Exception as e:
            logger.error(f"Failed to initialise application: {str(e)}")
            raise

    async def handle_file_upload(self) -> Optional[str]:
        """Handle resume file upload"""
        uploaded_file = st.file_uploader(
            "Upload your resume (PDF format)", type=["pdf"]
        )

        if uploaded_file and not st.session_state.resume_uploaded:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                temp_file.write(uploaded_file.getvalue())
                temp_path = temp_file.name

            try:
                reader = PdfReader(temp_path)
                resume_text = ""
                for page in reader.pages:
                    resume_text += page.extract_text()

                st.session_state.resume_uploaded = True
                st.session_state.resume_text = resume_text
                return resume_text
            except Exception as e:
                st.error(f"Error processing resume: {str(e)}")
                logger.error(f"Error processing resume: {str(e)}")
            finally:
                os.unlink(temp_path)

        return None

    async def process_message(self, message: str) -> str:
        """Process user message and generate response"""
        try:
            if not st.session_state.resume_uploaded:
                return "Please upload your resume first to get personalized recommendations."

            # Get relevant jobs
            relevant_jobs = await self.vector_store.search(st.session_state.resume_text)

            # Generate response using LLM
            response = await self.llm_service.generate_response(
                question=message,
                resume_text=st.session_state.resume_text,
                relevant_jobs=relevant_jobs,
            )

            return response
        except Exception as e:
            logger.exception("Error processing message")
            return f"Sorry, I encountered an error: {str(e)}"

    def render(self):
        """Render the application interface"""
        st.title("AI Career Coach 👔")

        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Resume upload
        asyncio.run(self.handle_file_upload())

        # Chat input
        if prompt := st.chat_input("Type your message here..."):
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})

            # Process message
            response = st.write_stream(asyncio.run(self.process_message(prompt)))

            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()


def main():
    """main entry point"""
    try:
        # Set page config
        st.set_page_config(page_title="AI Career Coach", page_icon="👔", layout="wide")

        app = Application()
        asyncio.run(app.initialise())
        app.render()

    except JobsAIException as e:
        st.error(f"Application error: {str(e)}")
    except Exception as e:
        st.error(f"UInexpected error: {str(e)}")
        logger.exception("Unexpected error in main application")


if __name__ == "__main__":
    main()
