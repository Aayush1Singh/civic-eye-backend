from services.gemini_summary_llm import llm_cycle
from langchain.prompts import PromptTemplate

prompt=PromptTemplate(input_variables=['current_summary','new_query','gemini_response'], template="""You are a specialized AI assistant for an Indian legal analysis tool. Your primary function is to maintain an accurate and evolving summary of legal discussions.

**Context:**
*   **Tool Focus:** Indian Legal System
*   **Current Summary:**
    ```
    {current_summary}
    ```
*   **Recent User Inquiry (Legal Question):**
    ```
    {new_query}
    ```
*   **Information Provided (Gemini's Legal Response):**
    ```
    {gemini_response}
    ```

**Your Task: Generate an Updated Legal Summary**
Revise and update the "Current Summary" by meticulously integrating the pertinent legal details from the "Information Provided." The update should specifically address or expand upon aspects related to the "Recent User Inquiry" with a strong focus on elements relevant to Indian law.

The goal is a single, cohesive, and legally precise updated summary. Aim for seamless integration rather than simple appending. Maintain neutrality and accuracy.You do not need to format text. Keep new summary as a small,concise,single, small paragrah.
JUST OUTPUT THE SUMMARY AND NO FORMATTING, HEADING IS NEEDED.DO NOT ADD A PRELUDE LIKE NEW UPDATED SUMMARY.
""")


def new_summary_generator(current_summary,new_chat):
  llm=next(llm_cycle)
  chain = prompt | llm
  output = chain.invoke({'gemini_response':new_chat['response'],'new_query':new_chat['query'],"current_summary":current_summary})
  # print(output.content)
  return output.content


# new_summary_generator('my name is Veena',{'query':'what is my name?','response':'Your name is aayush'})
