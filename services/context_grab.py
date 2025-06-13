from upstash_vector import Index
from langchain_community.vectorstores.upstash import UpstashVectorStore
from services.gemini_embedder import embedder_cycle
import os
from dotenv import load_dotenv
import asyncio
from concurrent.futures import ThreadPoolExecutor
_executor = ThreadPoolExecutor()
from services.redis_upstash import get_index
load_dotenv()
async def context_grab(query):
  url,token=await get_index('namespaces')
  index_classifier = Index(url=f"https://{url}", token=token)
  url,token=await get_index('acts')
  index_main=Index(url=f"https://{url}", token=token)
  # query="i am being harrased by a loan agent"
  model=next(embedder_cycle)
  vectors = model.embed_query(query)
  op=index_classifier.query(
  vector=vectors,
  include_metadata=True,
  include_data=False,
  include_vectors=False,
  top_k=4,
  )
  final_context=""
  print(op)
  
  for i in op:
    print(i)
    namespace=i.metadata['namespace']
    vectorstore=UpstashVectorStore(
        embedding=model,
        index_url=os.getenv("UPSTASH_VECTOR_REST_URL"),
        index_token=os.getenv("UPSTASH_VECTOR_REST_TOKEN"),
        index=index_main,
        namespace=namespace
      )
    retriever=vectorstore.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={'score_threshold': 0.3}
      )
    loop = asyncio.get_running_loop()
    docs=await loop.run_in_executor(_executor, lambda: retriever.invoke(query))
    relevant_docs = [doc.page_content for doc in docs if doc.page_content.strip()]
    if(len(relevant_docs)==0): 
      continue
    final_context+="\nContext from "+namespace
    for i in relevant_docs:
      final_context+="\n"+i
    # print(i.metadata['namespace'])
  return final_context
# print(get_index, type(get_index))
# print(asyncio.run(context_grab("i am being forced into unatural acts, what should i do?")))