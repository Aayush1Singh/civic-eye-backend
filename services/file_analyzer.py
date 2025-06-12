
# from pdf2image import convert_from_path
from services.supabase_buckets_initialise import supabase
# from pdf2image import convert_from_path, convert_from_bytes
from services.get_sessions import write_analysis_to_history
# import cv2
# import numpy as np
# import pytesseract
import os
from services.get_sessions import write_chat_to_history
from services.get_sessions import get_summary

import fitz  # PyMuPDF
from PIL import Image
import io
import string
import re
from services.pdf_parser import parse_and_clean_pdf
from services.gemini_embedder import embedder_cycle
# from cleantext import clean
# from textblob import TextBlob
from langchain.prompts import PromptTemplate
from functools import reduce
from services.gemini_chat_llm import llm_cycle
from services.redis_upstash import get_index
from upstash_vector import Index
from langchain_community.vectorstores.upstash import UpstashVectorStore
import asyncio
from concurrent.futures import ThreadPoolExecutor

SUPPRESS_OSD_WARNINGS = True  # Set to False if you want Tesseract OSD console output
PDF_DPI = 300               # Increase DPI for sharper text (300 dpi is a common choice)
OUTPUT_FOLDER = "processed_pages"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
from PIL import Image
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def load_pdf(session_id,last_id):
  # Attempt to download the file from the "avatars" bucket
  print(f'{session_id}/{last_id}.pdf')
  loop = asyncio.get_running_loop()
  with ThreadPoolExecutor() as executor:
    file_data = await loop.run_in_executor(
      executor,
      lambda: supabase.storage.from_('file-storage').download(f"{session_id}/{last_id}.pdf"))
  # file_data = supabase.storage.from_('file-storage').download(f'{session_id}/{last_id}.pdf')
  with open(f'user_data/{session_id}.pdf', "wb") as f:
    f.write(file_data)

def delete_pdf(session_id):
  os.remove(f'user_data/{session_id}.pdf')
  
# def pdf_to_images(pdf_path: str, dpi = PDF_DPI):
#     """
#     Convert each page of the PDF into a PIL Image at the given DPI.
#     Returns a list of PIL.Image objects, one per page.
#     """
#     doc = fitz.open(pdf_path)
#     images = []

#     for page_num in range(len(doc)):
#         page = doc.load_page(page_num)
#         pix = page.get_pixmap(dpi=200)
#         img = Image.open(io.BytesIO(pix.tobytes("png")))
#         images.append(img)
#     return images
  
#     # convert_from_path returns a list of PIL Images
#     images = convert_from_path(pdf_path, dpi=dpi)
#     return images


# def osd_rotate(pil_img):
#     """
#     Uses pytesseract.image_to_osd to detect full-page rotation (0, 90, 180, 270),
#     then rotates the PIL image to upright. If no rotation is detected, returns the original.
#     """
#     # Convert PIL → grayscale OpenCV
#     cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2GRAY)

#     # Suppress console logs from Tesseract if desired
#     custom_oem_psm = "--oem 3 --psm 0"
#     if SUPPRESS_OSD_WARNINGS:
#         pytesseract.pytesseract.tesseract_cmd = pytesseract.pytesseract.tesseract_cmd  # no-op
#         osd_data = pytesseract.image_to_osd(cv_img, output_type=pytesseract.Output.DICT, config=custom_oem_psm)
#     else:
#         osd_data = pytesseract.image_to_osd(cv_img, output_type=pytesseract.Output.DICT, config=custom_oem_psm)

#     rotation_angle = osd_data.get("rotate", 0)
#     if rotation_angle != 0:
#         # PIL.rotate rotates counterclockwise; to undo a clockwise rotation use a negative angle
#         return pil_img.rotate(-rotation_angle, expand=True)
#     return pil_img


# # -----------------------------------------
# # 3) Deskew at arbitrary angle (± a few degrees)
# # -----------------------------------------
# def deskew_image(pil_img):
#     """
#     Finds the smallest bounding box around dark pixels (assumes text is darker than background),
#     computes its angle, and rotates the image to deskew if needed.
#     """
#     # Convert PIL → grayscale OpenCV
#     cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2GRAY)

#     # Binarize: text (dark) → white, background → black
#     # Use OTSU to auto‐select threshold
#     _, bw = cv2.threshold(cv_img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

#     # Find coordinates of all non-zero (i.e. text) pixels
#     coords = np.column_stack(np.where(bw > 0))
#     if coords.size == 0:
#         # No text found; return original
#         return pil_img
#     # Compute minimum-area bounding rectangle around text pixels
#     rect = cv2.minAreaRect(coords)
#     angle = rect[-1]
#     # The angle returned by minAreaRect is between -90 and 0.
#     # We convert it to the correct “deskew” angle.
#     if angle < -45:
#         angle = angle + 90
#     # If skew is very small (< 0.5°), skip rotating
#     if abs(angle) < 0.5:
#         return pil_img
#     # Rotate the original PIL image by -angle degrees
#     return pil_img.rotate(-angle, expand=True)

# def ocr_image(pil_img, lang = "eng"):
#     """
#     Runs Tesseract OCR on the (already deskewed/rotated) PIL image and returns the extracted text.
#     """
#     return pytesseract.image_to_string(pil_img, lang=lang)


# # -----------------------------------------
# # 5) Main pipeline
# # -----------------------------------------

# def process_pdf_for_ocr(pdf_path):
#     """
#     - Converts PDF pages to images
#     - Auto-rotates 90°‐steps
#     - Deskews small angles
#     - Runs Tesseract OCR
#     - Saves corrected images (optional) and prints extracted text
#     """
#     images = pdf_to_images(pdf_path)
#     content=[]
#     for idx, page_img in enumerate(images, start=1):
#         try:
#             # Step A: OSD-based 90° rotation
#             rotated = osd_rotate(page_img)
#             # Step B: OpenCV-based deskew
#             deskewed = deskew_image(rotated)
#             # (Optional) Save intermediate deskewed image for inspection
#             out_filename = os.path.join(OUTPUT_FOLDER, f"page_{idx:03d}_corrected.png")
#             deskewed.save(out_filename, format="PNG")
#             # Step C: Run OCR
#             text = ocr_image(deskewed)
#             print(f"\n--- OCR Text from Page {idx} ---\n")
#             filtered_content=preprocess_text(text,idx)
#             print(filtered_content)
#             content.append(filtered_content)
#             # print(filtered_content)
#             print("\n-------------------------------\n")

#         except Exception as e:
#             print(f"[Error] Page {idx} failed: {e}")
#     return content
# def preprocess_text(text,page_no):
#     text = clean(
#     text,
#     fix_unicode=True,       # Fixes accents/encoding
#     to_ascii=True,          # Converts to closest ASCII
#     lower=False,
#     no_line_breaks=True,
#     no_urls=True,
#     no_emails=True,
#     no_phone_numbers=True,
#     no_numbers=False,
#     no_digits=False,
#     replace_with_punct="",
#     replace_with_url="<URL>",
#     replace_with_email="<EMAIL>",
# )    
#     lines=text.split('.');
#     new_lines=[]
#     for i in lines:
#         if(len(set(i))<=len(str(page_no+1))):
#             continue
#         else: 
#             new_lines.append('.'+re.sub(r'\s+', ' ', i))
            
#     # print("hello ",new_lines)
#     new_str= str(reduce(lambda x,y:x+y,new_lines))
    
#     new_str=''.join(c for c in new_str if c in string.printable)
#     # print(new_str)
#     blob = TextBlob(new_str)
#     return str(blob.correct())

prompt_clause_generator=PromptTemplate(template="""You are a legal document parser. Your task is to extract and structure key clauses from a legal document (delimited by @@@), grouping them under finite, broader thematic headings (e.g., “Eligibility,” “Payment Terms,” “Termination”,"Accusations") rather than assigning a unique title to each individual clause. If the given text is not a legal document, return an empty JSON array.

Instructions:
1. **Detect Legal Document or Not**  
   • If the provided text does not resemble a contract or legal or criminal(e.g. ChargeSheet, FIR ) document (e.g., it lacks numbered sections, headings, obligations/rights language, or clearly identified parties), return an empty list: `[]`.
2. **Discard Non-Legal Sections**  
   Completely ignore general introductions, preambles, recitals, background descriptions, contact info, document metadata, and boilerplate opening text.  
   Do **not** include greetings (e.g., "This Agreement is made on...") unless they define parties or legal terms.  
   Focus only on sections that define **obligations, rights, responsibilities, procedures, legal conditions, dispute mechanisms, liabilities, warranties, or terms**.
3. **Pre-Processing & Noise Handling**  
   • Remove any obvious OCR artifacts or formatting noise (broken lines, repeated page numbers, stray punctuation).  
   • Preserve all legally relevant terms, numbers, and stop-words (e.g., “unless,” “party,” “defined terms”).

4. **Identify Broad Clause Divisions**  
   • Scan the text for high-level section or division indicators such as “1. Eligibility,” “Section 5: Eligibility Criteria,” “Article X - Eligibility,” or any clear heading/numbering scheme (e.g., “2. Confidentiality,” “3. Payment”).  
   • If headings are missing, look for recurring thematic language (e.g., multiple paragraphs describing who is allowed to participate, qualifications, or conditions) and assign those to a single thematic heading called **“Eligibility.”**  
   • Common broad headings include (but are not limited to):  
      **“Definitions”** (where terms are explained)  
      **“Eligibility”** (criteria or qualifications)  
      **“Payment Terms”** or **“Compensation”**  
      **“Confidentiality”**  
      **“Termination”** or **“Cancellation”**  
      **“Liability”** or **“Indemnification”**  
      **“Governing Law”** or **“Jurisdiction”**  
      **“Intellectual Property”**  
      **“Dispute Resolution”**  
      **“Force Majeure”**  
      **“Representations & Warranties”**  
      **“Limitation of Liability”**  
      **“Notices”**  
   • If several clauses or paragraphs fall under the same theme (e.g., multiple eligibility requirements appear in non-contiguous places), group them all under one **“Eligibility”** entry rather than making separate “Eligibility 1,” “Eligibility 2,” etc. 

5. **For Each Grouped Division, Produce One Object**  
   • **`"title"`**: Use the exact heading if present (e.g., `"Eligibility"`, `"Payment Terms"`). If a heading is not explicit, infer a concise title that best captures the group's subject (e.g., `"Termination"`, `"Liability"`).  
   • **`"text"`**: Concatenate all paragraphs or sentences that belong to this division, preserving original order and punctuation. Include line breaks between paragraphs for readability.

6. **Output Format**  
     [
       {{
         "title": "Eligibility",
         "text": "Any natural person aged 18 or over may apply. The applicant must provide proof of residency... [and so on, combining all eligibility paragraphs]"
       }},
       {{
         "title": "Payment Terms",
         "text": "The client shall pay the service fee of ₹50,000 within 30 days of invoice date. Late payments will incur interest at 18% per annum... [combined paragraphs]"
       }},
       {{
         "title": "Termination",
         "text": "This agreement may be terminated by either party with 30 days written notice. In the event of breach, the non-breaching party may terminate immediately... [combined paragraphs]"
       }}
       // … additional grouped divisions …
     ]
     

7. **Additional Notes**  
   #### Only use a limited number of titles (you are free to use a broader terms to maintain limited number of unique titles)
   #### Each clause should have its own object
   #### Ignore any lines that are clearly not part of a clause (e.g., table of contents, page numbers, administrative footers).  
   #### Do not invent headings that do not match any legal theme; only infer a title when a clear thematic pattern emerges.  
   #### Ensure the final JSON is syntactically valid and contains no extra commentary or explanatory text.
   #### Do **not** wrap the response in triple backticks or code fences.  
   #### Do **not** include explanations or commentary.  
   #### Only return the array directly.
   #### If a clause if too large split it into many clauses(each clause with different object) under the same title.
   #### Remember to return only a list of object (in case no object found, return a empty list([]))
Contract text:
@@@{contract_text}@@@
""",input_variables=['contract_text',])
prompt_summary_generator=PromptTemplate(template="""You are a legal summarization assistant. Below is the full text of a contract (delimited by @) (OCR-cleaned). Produce a concise summary that includes:
1.The type of contract (e.g., “Sales Agreement,” “NDA”).
2.The number of parties involved and their names (e.g., “between Alpha Tech and Beta Solutions”).
3.How those parties are related (e.g., “service provider and client,” “buyer and seller,” “licensor and licensee”).
4.Its high-level purpose (e.g., “providing software-as-a-service,” “sale of goods,” “licensing intellectual property”).
5.Do not include any meta commentary
6.If any Non understandable words/ gibberish found, ignore them.

Return exactly one or two sentences—no more.

Preview of Contract:
@{preview}@
""",input_variables=['preview'])
prompt_summary_type=PromptTemplate(template="""You are a legal-domain classifier. Below is a very brief summary(delimited by @@) of a contract or legal document. Your job is to choose, from the list of available legal domain labels, all those labels whose corresponding vector store would likely contain statutes, case-law, or commentary directly relevant to analyzing this document.

Here are the labels and their corresponding vector indices:
  1. "rights"                   → "constitution-vector"
  2. "substantive criminal law" → "bns-vector"
  3. "criminal procedure"       → "bnss-vector"
  4. "corporate law"            → "company-vector"
  5. "contract law"             → "contract-vector"
  6. "consumer protection law"  → "consumer-vector"
  7. "evidence law"             → "evidence-vector"

Instructions:
  1. Read the DOC_CONTEXT carefully—it describes the type of contract and its main purpose.
  2. Select all labels whose legal domain is likely needed for in-depth analysis of this document.  
    # For instance, if the document is a “Sales Agreement,” you would choose "contract law" (→ "contract-vector").  
    # If it involves share-issuance or corporate governance, include "corporate law" (→ "company-vector").  
    # If it discusses consumer warranties or product liability, include "consumer protection law" (→ "consumer-vector").  
  3. If a summary involves multiple legal aspects (e.g., it's both a “franchise agreement” and “consumer financing”), you may pick more than one label (e.g., "contract law" and "consumer protection law").
  4. Only return a array of the exact vector indices strings (from the seven keys above). Do not output any extra text.
  5. Do not add any meta commentary.

Example output format:
['evidence-vector','consumer-vector']

@@{summary}@@
""",input_variables=['summary'])

chain_analysis=PromptTemplate(template= """You are a legal-domain assistant. Below is a brief preview of the overall contract (“DOCUMENT_PREVIEW”), a single block of relevant Indian law passages (“LAW_CONTEXT”) retrieved via embeddings, and a batch of clauses (“CLAUSE_LIST”). Analyze each clause in light of the DOCUMENT_PREVIEW and the LAW_CONTEXT, and produce a structured  array it can be sent directly to our frontend. Please use your latest general knowledge in reference to indian laws in case if the LAW_CONTEXT is not enough or not related to question asked.

For each clause, do all of the following:

1. **Identify Parties & Relationships**  
   • From the DOCUMENT_PREVIEW, state how many parties are involved, their names (if given), and their roles (e.g., “Alpha Tech (service provider) and Beta Solutions (client)”).  
   • If the clause refers to “Party A” or “Party B,” map those labels to the actual names/roles from DOCUMENT_PREVIEW.  
   • Return this as a string under `"identified_parties"`.

2. **Bias Flags**  
   • Highlight any sentence or phrase in the clause that unduly favors one party over another (e.g., “Party A may terminate without cause”).  
   • Return these as an array of strings under `"bias_flags"`.  
   • If there are no such phrases, return an empty array.

3. **Ambiguities**  
   • Point out any vague or undefined terms (e.g., “reasonable efforts,” “material breach,” “the Company”).  
   • Return these as an array of strings under `"ambiguities"`.  
   • If none, return an empty array.

4. **Potential Loopholes**  
   • Identify language that a counterparty could exploit to evade obligations (e.g., “no cap on liability,” “Party X may terminate at any time”).  
   • Return these as an array of strings under `"potential_loopholes"`.  
   • If none, return an empty array.

5. **Legal Conflicts**  
   • Using the single LAW_CONTEXT block (Indian statute or constitutional excerpts), check whether any part of this clause directly contradicts or conflicts with the LAW_CONTEXT.  
   • For each conflict, explain briefly how the clause runs counter to the law passage.  
   • Return these as an array of strings under `"legal_conflicts"`.  
   • If no conflicts are detected, return an empty array.

6. **Improvements (Optional)**  
   • If the clause has any entries in “bias_flags”, “ambiguities”, “potential_loopholes”, or “legal_conflicts”, suggest one or more bullet-pointed improvements or alternative language to correct those issues.  
   • Return these as an array of strings under `"improvements"`.  
   • If the clause has no issues (i.e., all arrays are empty), omit the `"improvements"` key entirely.

7. **Bias Score**  
   • Assign a numeric score between 0.00 and 1.00 that indicates how heavily biased the clause is (0.00 = fully balanced; 1.00 = extremely one-sided).  
   • Return this as a float under `"bias_score"`.

**Return exactly one array**, nicely formatted (indented with two spaces), containing one object per clause in the same order as in CLAUSE_LIST. **Do not** include any extra text outside the array.
**Ensure the final array is syntactically valid and contains no extra commentary or explanatory text.**
**Do not wrap the response in triple backticks or code fences.**  
**Do not include explanations or commentary.**  
**Only return the array directly.**

DOCUMENT_PREVIEW:
"{summary}"

LAW_CONTEXT:

{context}

CLAUSE_LIST:
{clauses}

Output:
[
  {{
    "bias_flags": [
      "“Party A may terminate without cause or notice.”"
    ],
    "ambiguities": [
      "“Written notice” is undefined—unclear how notice must be given."
    ],
    "potential_loopholes": [
      "No force majeure carve-out—could force Beta Solutions to pay even if performance is impossible due to natural disasters."
    ],
    "legal_conflicts": [
      "Conflict with ICA_75: court may reduce penalty if clause's termination penalty is deemed unreasonable."
    ],
    "improvements": [
      "Define “written notice” explicitly (e.g., 'notice via registered mail delivered 30 days prior').",
      "Add a force majeure clause to exempt liability under specified events."
    ],
    "bias_score": 0.85
  }},
  {{
    "bias_flags": [],
    "ambiguities": [
      "“Proprietary information” is undefined—scope is unclear."
    ],
    "potential_loopholes": [
      "No requirement to destroy or return confidential materials upon termination."
    ],
    "legal_conflicts": [],
    "improvements": [
      "Define “proprietary information” clearly (e.g., 'Confidential Information includes customer data, source code, financial details').",
      "Add return/destruction requirement upon termination."
    ],
    "bias_score": 0.30
  }},
  {{
    "bias_flags": [],
    "ambiguities": [],
    "potential_loopholes": [],
    "legal_conflicts": [],
    "bias_score": 0.00
  }}
  // …additional clause objects as needed…
]

""",input_variables=['context','clauses','summary'])

async def  analyze_document(session_id=None,user_id=None):
  # sess
  current_summary,new_upload,last_id=get_summary(session_id,user_id)
  await load_pdf(session_id,last_id)
  loop = asyncio.get_running_loop()
  with ThreadPoolExecutor() as executor:
    content = await loop.run_in_executor(
      executor,
      lambda: parse_and_clean_pdf(f'user_data/{session_id}.pdf'))

  # content=parse_and_clean_pdf(f'user_data/{session_id}.pdf')
  llm=next(llm_cycle)
  chain_clauses = prompt_clause_generator | llm
  chain_summary=prompt_summary_generator | llm
  chain_type=prompt_summary_type | llm
  final_text=content
  temp=content.split('.')
  final_preview=temp[:min(len(temp),100)]
  
#   for i in range(len(content)):
#       if(len(content[i])>0):
#           final_text+='\n'+f"Content from Page {i}\n"+content[i]

#       if(i<8 and len(content[i])>0):
#           final_preview+='\n'+f"Content from Page {i}\n"+content[i]
          
  clauses= await chain_clauses.ainvoke({'contract_text':final_text})
  print('Clauses:->->->->')
  print(clauses, type(clauses))
  clauses=eval(clauses)
  print('Clauses:->->->->')
  print(clauses, type(clauses))
  summary=await chain_summary.ainvoke({'preview':final_preview})
  print('Summary:->->->->')
  print(summary,type(summary))
  context_type=eval(await chain_type.ainvoke({'summary':summary}))
  print('Context-type->->->')
  print(context_type)
  final_analysis= chain_analysis | llm
  embedding =next(embedder_cycle)
  retriever_list=[]
  dictionary_grp={}
  for i in clauses:
      if i['title'] not in dictionary_grp:
        dictionary_grp[i['title']]=[i['text'],]
      else:
          dictionary_grp[i['title']].append(i['text'])
    
  for index_name in context_type:
    try:
      url,token=await get_index(index_name)
      index = Index(url=f"https://{url}", token=token)
      vectorstore = UpstashVectorStore(
      embedding=embedding,
      index_url=os.getenv("UPSTASH_VECTOR_REST_URL"),
      index_token=os.getenv("UPSTASH_VECTOR_REST_TOKEN"),
      index=index,
      )
    except Exception as e:
      continue    
    retriever=vectorstore.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={'score_threshold': 0.5}
    )
    retriever_list.append(retriever)

  final_output=[]
  # loop = asyncio.get_running_loop()
  for key,clauses in dictionary_grp.items():
    for i in range(0,len(clauses),5):
        clauses_text=''
        final_context=""
        for j in range(i,min(len(clauses),i+5)):
            clauses_text=clauses_text+clauses[j]
        for retriever in retriever_list:
            with ThreadPoolExecutor() as executor:
              docs=await loop.run_in_executor(executor, lambda: retriever.invoke(clauses_text))
            # docs = retriever.invoke(clauses_text)
            relevant_docs = [doc.page_content for doc in docs if doc.page_content.strip()]  
            final_context+=str(reduce(lambda x,y:x+y,relevant_docs))
        output=await final_analysis.ainvoke({'clauses':clauses[i:min(len(clauses),i+5)],'context':final_context,'summary':summary})
        output=eval(output)
        for j in range(i,min(len(clauses),i+5)):
            output[j-i]['clause']=clauses[j]
        final_output.extend(output)
        
  delete_pdf(session_id)
  print(final_output)
  write_analysis_to_history(final_output,session_id,last_id)

  # current_summary=get_summary(session_id,user_id)
  
  print("Current- summary:->->")
  print(summary)
  
  write_chat_to_history(session_id,current_summary,{"query":"Used analyzed document","response":f"Analysis complete. Found ${len(final_output)} clauses, with ${0} clauses showing high bias scores. See the detailed analysis report for more information.","analysedDoc":True,"fileUpload":True,'doc_id':last_id})

  return final_output

  

