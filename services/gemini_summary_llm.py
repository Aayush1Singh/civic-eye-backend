import itertools
import os
from dotenv import load_dotenv
from uuid import uuid4
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationSummaryMemory
from langchain.memory.chat_message_histories import RedisChatMessageHistory

load_dotenv()
GEMINI_LIST = eval(os.getenv("GEMINI_KEY_LIST"))

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
