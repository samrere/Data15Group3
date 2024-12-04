import streamlit as st
from components.chat_interface import ChatInterface
from config.settings import load_env_var


def main():
    load_env_var()

    # Set page config
    st.set_page_config(
        page_title="Jobs AI",
        page_icon="👔",
        layout="wide",
    )

    # Initialise chat interface
    chat_interface = ChatInterface()
    chat_interface.render()


if __name__ == "__main__":
    main()
