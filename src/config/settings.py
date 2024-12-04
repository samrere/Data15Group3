import os
from dotenv import load_dotenv


def load_env_var():
    """Load environment variables from .env file"""
    load_dotenv()

    # Verify required environment variables
    required_vars = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )
