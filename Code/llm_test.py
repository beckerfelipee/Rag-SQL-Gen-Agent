from Code.functions import test_model
from dotenv import load_dotenv
from langchain_community.chat_models import ChatOllama
import os
from Code import config as cfg


if __name__ == '__main__':
    # Load environment variables from .env file
    load_dotenv()

    # Initialize the model
    base_url = os.getenv("OLLAMA_LOCAL_SERVER") if cfg.RUN_LOCALLY else os.getenv("OLLAMA_SERVER")

    # Initialize the model
    llm = ChatOllama(base_url=base_url, model=cfg.LLM_MODEL, temperature=cfg.LLM_TEMPERATURE)

    # Test the model
    test_model(llm=llm)
    print("Test completed.")


