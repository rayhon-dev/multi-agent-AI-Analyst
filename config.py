import os

from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# All Gemini calls are routed through an OpenAI/Gemini-compatible proxy
# instead of calling Google directly.
PROXY_BASE_URL = "https://saidazam-litellm-proxy.hf.space/v1"

LLM_MODEL_LITE = "gemini-flash-lite"  # most/high-volume calls
LLM_MODEL_FLASH = "gemini-flash-lite"  # supervisor and critic (key can't access gemini-flash)
EMBEDDING_MODEL = "gemini-embedding"

if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY is missing. Add it to a .env file in the project root "
        "(get a free key at https://aistudio.google.com/apikey)."
    )
