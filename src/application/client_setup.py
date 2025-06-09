from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
DOTENV_PATH = ".env.azure"
load_dotenv(dotenv_path= DOTENV_PATH)


LLM_ENGINE = init_chat_model("openai/gpt-4")