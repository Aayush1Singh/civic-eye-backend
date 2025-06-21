import itertools
import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAI

load_dotenv()
GEMINI_LIST = eval(os.getenv('GEMINI_KEY_LIST'))

llm_pool = [
    GoogleGenerativeAI(
        model="gemini-2.5-flash-preview-05-20",
        google_api_key=key,
        temperature=1,
    )
    for key in GEMINI_LIST
]
llm_cycle = itertools.cycle(llm_pool)  



