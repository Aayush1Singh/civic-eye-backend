from langchain_community.vectorstores.upstash import UpstashVectorStore
import os
from gemini_embedder import embedder_cycle
from dotenv import load_dotenv
load_dotenv()
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import TextLoader

store = UpstashVectorStore(
    embedding=next(embedder_cycle),
    index_url=os.getenv("UPSTASH_VECTOR_REST_URL"),
    index_token=os.getenv("UPSTASH_VECTOR_REST_TOKEN")
)


loader = TextLoader("../../modules/state_of_the_union.txt")

documents = loader.load()
text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
docs = text_splitter.split_documents(documents)

# Create a new embeddings object
# Create a new UpstashVectorStore object
# Insert the document embeddings into the store
store.add_documents(docs)