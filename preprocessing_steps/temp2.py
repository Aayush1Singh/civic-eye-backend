from langchain_community.vectorstores import Redis
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
load_dotenv()
import os

GEMINI_LIST=eval(os.getenv('GEMINI_KEY_LIST'))
embedding = embeddings = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001",     # Gemini embedding model
    google_api_key=GEMINI_LIST[0]
)  # or your embedding function

index_name = "constitution_vector"

# Load vector store

vectorstore = Redis(
    redis_url="redis://localhost:6379", 
    index_name=index_name,
    embedding=embedding
)
# Run a similarity search
retriever=vectorstore.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={'score_threshold': 0.6}
)

docs = retriever.get_relevant_documents("What is Article 21?")

for i, res in enumerate(docs):
    print(res.page_content)

# results = vectorstore.similarity_search("What is Article 21", k=10)

# for i, res in enumerate(results):
#     print(res.page_content)
