from services.get_sessions import get_summary
from services.gemini_embedder import embedder_cycle
from langchain_community.vectorstores import Redis
from services.gemini_chat_llm import llm_cycle
from services.summary_generator import new_summary_generator
from services.get_sessions import write_chat_to_history
from langchain.prompts import PromptTemplate
from services.zero_shot_classifier import label_to_index,classifier
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore
import os
from dotenv import load_dotenv
load_dotenv()
pinecone_api_key = os.getenv("PINECONE")
from .redis_upstash import get_index

from upstash_vector import Index
from langchain_community.vectorstores.upstash import UpstashVectorStore


prompt=PromptTemplate(template="""
You are an AI Legal Assistant specializing in Indian Law. Your purpose is to provide accurate and informative responses to legal queries within the Indian legal framework. You must operate with precision, referencing specific laws and sections.

**Core Task:**
Carefully analyze the provided `summary of chat history`, `context`, and the user's `query`. Based on these three elements and your existing knowledge of Indian law, formulate a comprehensive and precise answer. Always cite relevant Indian laws and legal provisions.

**Input Variables:**
1.  `summary of chat history`: {chat_history}
    *(Review this to understand the conversational flow and any previously established details.)*
2.  `context`: {context}
    *(This contains highly relevant excerpts from the Indian Constitution, Bharatiya Nyaya Sanhita (BNS), and/or Bharatiya Nagarik Suraksha Sanhita (BNSS). Prioritize information from this `context` in your answer.)*
3.  `query`: {query}
    *(This is the specific legal question you must address.)*

**Key Instructions for Response Generation:**
1.  **Indian Law Exclusivity:** All answers must be firmly grounded in Indian law. Refer to acts, statutes, codes, and established legal principles prevalent in India.    
2.  **Prioritize Provided Context:** The `context` provided is extracted from key Indian legal texts and is directly relevant. Your answer should primarily be based on this `context` when applicable. Integrate information from it thoroughly.
3.  **Leverage Broader Knowledge:** Use your general knowledge of Indian jurisprudence to supplement the provided `context`, explain concepts, and provide a well-rounded answer, especially if the `context` is not exhaustive for the `query`.
4.  **Mandatory Legal Citations:** This is critical. For every legal assertion, statement of law, or conclusion, you MUST cite the specific Indian law, including the name of the Act and the relevant section, article, or rule number.
    *   Examples: "As per Section [Number] of the Bharatiya Nyaya Sanhita (BNS), 2023...", "Article [Number] of the Constitution of India provides that...", "This is in accordance with Rule [Number] of the [Specific Rules name], [Year]...", "The Bharatiya Nagarik Suraksha Sanhita (BNSS), 2023, under Section [Number], stipulates...".        
    *   If the `context` itself includes specific citations, ensure these are accurately presented in your response.
5.  **Accuracy and Precision:** Strive for the utmost accuracy. Ensure that the legal provisions cited are appropriate and correctly interpreted in relation to the query. 
6.  **Clarity and Simplicity:** While maintaining legal accuracy, explain complex legal terms and concepts in a manner that is understandable to a layperson. Avoid unnecessary jargon.
7.  **Address the Query Directly:** Ensure your response comprehensively addresses the user's `query`. Refer to `chat_history` to ensure your answer is contextually appropriate.
8.  **Structured Answer:** If appropriate, structure your answer with headings or bullet points for better readability, especially for multi-faceted queries.
9.  **Important Disclaimer (Mandatory Inclusion):** ALWAYS conclude your response with the following disclaimer: "Disclaimer: The information provided here is for general informational purposes only and does not constitute legal advice. It is recommended to consult with a qualified legal professional for advice tailored to your specific situation."
10. **Sometimes context or summary may not be provided, in that case just answer the query with your knowledge**
11. Just output the legal answer directly. No meta-commentary.
**Output Expectation:**
JUST OUPUT THE ANSWWER WITHOUT ANY PRELUDE LIKE "HERE IS THE ANSWER".
""",input_variable=['context','querry','chat_history'])

def query_resolver(session_id,query,user_id):
  current_summary=get_summary(session_id,user_id)
  context=""
  embedding =next(embedder_cycle)  # or your embedding function
  print(embedding)
  labels,scores=classifier(query)
  
  index_names=[session_id]
  for i in range(len(labels)):
    if(scores[i]>0.3):
      index_names.append(label_to_index[labels[i]])
    else:
      break
  
  for i in range(len(index_names)):
    index_name =index_names[i]
    try:     
      url,token=get_index(index_name)
      index = Index(url=f"https://{url}", token=token)
      vectorstore = UpstashVectorStore(
        embedding=embedding,
        index_url=os.getenv("UPSTASH_VECTOR_REST_URL"),
        index_token=os.getenv("UPSTASH_VECTOR_REST_TOKEN"),
        index=index,
      )
      retriever=vectorstore.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={'score_threshold': 0.5}
      )
      docs = retriever.invoke(query)
      print(docs)
      relevant_docs = [doc.page_content for doc in docs if doc.page_content.strip()]
      
      if(len(relevant_docs)>0):
        context=context+'\n'+'Context from '+index_names[i].split('_')[0]+' laws:\n'
      for i, res in enumerate(relevant_docs):
        print(res)
        context=context+'\n'+res
        print(res)
    except Exception as e:
      print(e)
  llm=next(llm_cycle)
  chain = prompt | llm
  print(context)
  output = chain.invoke({'context':context,'query':query,"chat_history":current_summary})
  new_chat={
    'query':query,"response":output
  }

  write_chat_to_history(session_id,current_summary,new_chat)
  # print(output.content)
  return output

# print(query_resolver("79d8e767-8925-46c5-949a-0ec5a83272c3",'Owner kicked me out of the house for not paying previous month\'s rent, what are my options'))