import streamlit as st
from typing import Optional
from utils.embedding import Embedding
from utils.llm import LLM
from utils.resumer_parser import ResumerParser
import tempfile
import os


class ChatInterface:
    def __init__(self):
        self.initialise_session_state()
        self.resume_parser = ResumerParser()
        self.embedding = Embedding()
        self.llm = LLM()

    def initialise_session_state(self):
        """Initialise session state variables"""
        if "messages" not in st.session_state:
            st.session_state.messages = [
                {
                    "role": "assistant",
                    "content": "Hey there! I'm your personal career coach. What position are you looking for? Please upload your resume & type the role you're interested in the chat input window and hit enter to start! ",
                }
            ]
        if "resume_uploaded" not in st.session_state:
            st.session_state.resume_uploaded = False

    def handle_file_upload(self) -> Optional[str]:
        """Handle resume file upload"""
        uploaded_file = st.file_uploader("Upload your resume (.pdf)", type=[".pdf"])

        if uploaded_file and not st.session_state.resume_uploaded:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name

            try:
                resume_text = self.resume_parser.process_resume(tmp_path)
                st.session_state.resume_uploaded = True
                return resume_text
            except Exception as e:
                st.error(f"Error processing resume: {str(e)}")
            finally:
                os.unlink(tmp_path)

        return None

    def render(self):
        """Render the chat interface"""
        st.title("AI Career Coach")

        # Display chat message
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Resume upload button
        resume_text = self.handle_file_upload()
        if resume_text:
            st.success("Resume uploaded")

        # Chat input
        if prompt := st.chat_input("Type your message here ..."):
            # Add user message to history
            st.session_state.messages.append({"role": "user", "content": prompt})

            try:
                # process user input and generate response
                if st.session_state.resume_uploaded:
                    response = self.llm.generate_response(
                        prompt,
                        resume_text,
                        self.embedding.get_relevant_jobs(resume_text),
                    )
                else:
                    response = (
                        "Please upload your resume first to get personalised feedback"
                    )

                # Add assistant response to chat history
                st.session_state.messages.append(
                    {"role": "assistant", "content": response}
                )
            except Exception as e:
                st.error(f"Error processing request: {str(e)}")
