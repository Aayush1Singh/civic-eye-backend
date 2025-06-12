# chat_manager.py
import itertools
import os
from dotenv import load_dotenv
# from uuid import uuid4

from langchain_google_genai import GoogleGenerativeAI
# from langchain.chains import ConversationChain
# from langchain.memory import ConversationSummaryMemory
# from langchain.memory.chat_message_histories import RedisChatMessageHistory

load_dotenv()
GEMINI_LIST = eval(os.getenv('GEMINI_KEY_LIST'))

# ── build an LLM pool ────────────────────────────────────────────
llm_pool = [
    GoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=key,
        temperature=1,
    )
    for key in GEMINI_LIST
]
llm_cycle = itertools.cycle(llm_pool)   # round-robin iterator



