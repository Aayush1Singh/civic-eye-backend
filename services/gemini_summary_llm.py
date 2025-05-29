import itertools
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()
GEMINI_LIST = eval(os.getenv('GEMINI_KEY_LIST'))

# ── build an LLM pool ────────────────────────────────────────────
llm_pool = [
    ChatGoogleGenerativeAI(
        model="gemini-1.5-flash-8b",
        google_api_key=key,
        temperature=1,
    )
    for key in GEMINI_LIST
]
llm_cycle = itertools.cycle(llm_pool)   # round-robin iterator

__all__=['llm_cycle']
