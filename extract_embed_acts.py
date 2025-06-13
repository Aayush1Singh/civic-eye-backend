import os
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from typing import List
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.schema import Document
import time
from urllib.parse import urljoin
import fitz  # PyMuPDF
import os
import re
import glob
from services.redis_upstash import create_index,get_index,delete_index
from upstash_vector import Index
from langchain_community.vectorstores.upstash import UpstashVectorStore
import numpy as np
from upstash_vector import Index, Vector
# from upstash_vector.types import DenseVector

# from sentence_transformers import SentenceTransformer
from services.gemini_embedder import embedder_cycle
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36",
    "Referer": "https://www.indiacode.nic.in/",
}

# Directory to save acts
OUTPUT_DIR = Path("indian_acts_pdfs")
OUTPUT_DIR.mkdir(exist_ok=True)
# URL of the central acts on IndiaCode
# BASE_URL = "https://www.indiacode.nic.in"
# CENTRAL_ACTS_URL = BASE_URL + "/handle/123456789/1362/simple-search?location=123456789/1362&offset="
BASE_URL='https://www.indiacode.nic.in/handle/123456789/1360/simple-search?query=act&filter_field_1=longtitle&filter_type_1=notcontains&filter_value_1=repeal&sort_by=dc.date.issued_dt&order=desc&rpp=100&etal=0&start='
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pathlib import Path

def is_index_page(lines):
    """Detect Table of Contents/index pages: many short lines with numeric section markers."""
    if len(lines) == 0:
        return True
    num_sec_markers = sum(1 for l in lines if re.match(r'^\d{1,3}\.\s', l))
    avg_len = sum(len(l) for l in lines) / max(len(lines), 1)
    # Index pages have many numeric markers and low average line length
    return num_sec_markers > 5 and avg_len < 40

def merge_hyphens(text):
    """Merge hyphenated words split at line break."""
    # Replace "-\n" with ""
    return re.sub(r'-\s*\n\s*', '', text)

def clean_text(text):
    """Generic cleaning: remove multiple hyphens, excessive whitespace."""
    text = merge_hyphens(text)
    # Remove lines of only hyphens or dots
    text = "\n".join(l for l in text.splitlines() if not re.fullmatch(r"[-. ]{5,}", l))
    # Collapse multiple blank lines
    text = re.sub(r'\n{2,}', '\n\n', text)
    return text.strip()

def find_main_content_start(doc):
    """
    Scan pages to find first page likely containing main content:
    - Looks for keywords like 'Short title', 'Definitions', 'Chapter', 'Section'
    """
    for i, page in enumerate(doc):
        text = page.get_text()
        if re.search(r'\b(Short title|Extent|Definitions|Chapter|Section)\b', text, re.IGNORECASE):
            return i
    return 0

def extract_high_quality_text(pdf_path):
    doc = fitz.open(pdf_path)
    start_idx = find_main_content_start(doc)
    full_text = []
    for page in doc[start_idx:]:
        text = page.get_text()
        lines = [l.strip() for l in text.splitlines()]
        # skip pages with too little content
        if len(lines) < 5:
            continue
        # skip index-like pages
        if is_index_page(lines):
            continue
        # join and clean lines
        page_text = "\n".join(lines)
        page_text = clean_text(page_text)
        # skip if still too short
        if len(page_text.split()) < 50:
            continue
        full_text.append(page_text)
    return "\n".join(full_text)
url,token=get_index('acts')
index = Index(url=f"https://{url}", token=token)
def chunk_text(text, chunk_size=500, chunk_overlap=50):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    chunks = splitter.split_text(text)
    return [Document(page_content=chunk) for chunk in chunks]

def embed_document(text, name):
    docs=chunk_text(text,2048,50)
    model=next(embedder_cycle)
    # vectorstore = UpstashVectorStore(
    #   embedding=model,
    #   index_url=os.getenv("UPSTASH_VECTOR_REST_URL"),
    #   index_token=os.getenv("UPSTASH_VECTOR_REST_TOKEN"),
    #   index=index,
    #   namespace=name
    #   )
    # print('hello debug')
    # vectorstore.add_documents(docs)
    # Compute centroid
    
    vectors = model.embed_documents([doc.page_content for doc in docs])
    centroid = np.mean(vectors, axis=0)

        ##################################################ADD THE INDEX


    index.upsert(
        vectors=[
            Vector(id=name, vector=centroid,metadata={'namespace':name}),
        ]
    )
    # Store centroid
    print('Centroid stored.')    # embeddings = model.encode(chunks)
    # save embeddings and raw chunks
    # import pickle
    # with open(os.path.join(output_dir, f"{name}_embeds.pkl"), "wb") as f:
    #     pickle.dump({"chunks": chunks, "embeddings": embeddings}, f)
def process_and_embed(pdf_path,name):
    try:
        text = extract_high_quality_text(pdf_path)
        if not text:
            print(f"[SKIP] No high-quality text extracted: {name}")
            return
        embed_document(text, name)
        os.remove(pdf_path)
    except Exception as e:
        print(f"[ERROR] {name}: {e}")

    # for pdf_file in glob.glob(os.path.join(pdf_dir, "*.pdf")):
    #     name = os.path.splitext(os.path.basename(pdf_file))[0]
    #     try:
    #         text = extract_high_quality_text(pdf_file)
    #         if not text:
    #             print(f"[SKIP] No high-quality text extracted: {name}")
    #             continue
    #         embed_document(text, name)
    #         os.remove(pdf_file)
    #         print(f"[DONE] Processed and embedded: {name}")
    #     except Exception as e:
    #         print(f"[ERROR] {name}: {e}")


# ─── CONFIG ────────────────────────────────────────────────────────

# Base search URL for India Code
# SEARCH_URL='https://www.indiacode.nic.in/handle/123456789/1360/simple-search?query=&filtername=title&filtertype=contains&filterquery=Protection+of+Children+from+Sexual+Offences+Act%2C+2012&rpp=10&sort_by=score&order=desc'

SEARCH_URL = "https://www.indiacode.nic.in/handle/123456789/1360/simple-search"

# Directory where PDFs will be saved
OUTPUT_DIR = Path("all_central_acts_pdfs")
OUTPUT_DIR.mkdir(exist_ok=True)

# Your full list of frequently used Central Acts
ACT_NAMES = [
    "Constitution of India, 1950",
    "Bharatiya Nyaya Sanhita, 2023",
    "Bharatiya Nagarik Suraksha Sanhita, 2023",
    "Bharatiya Sakshya Adhiniyam, 2023",
    "Code of Civil Procedure, 1908",
    "Indian Contract Act, 1872",
    "Transfer of Property Act, 1882",
    "Specific Relief Act, 1963",
    "Limitation Act, 1963",
    "Arbitration and Conciliation Act, 1996",
    "Negotiable Instruments Act, 1881",
    "Companies Act, 2013",
    "Insolvency and Bankruptcy Code, 2016",
    "Goods and Services Tax Act, 2017",
    "Hindu Succession Act, 1956",
    "Indian Trusts Act, 1882",
    "Hindu Marriage Act, 1955",
    "Hindu Adoption and Maintenance Act, 1956",
    "Special Marriage Act, 1954",
    "Indian Divorce Act, 1869",
    "Parsi Marriage and Divorce Act, 1936",
    "Muslim Personal Law (Shariat) Application Act, 1937",
    "Dissolution of Muslim Marriages Act, 1939",
    "Muslim Women (Protection of Rights on Divorce) Act, 1986",
    "Protection of Women from Domestic Violence Act, 2005",
    "Dowry Prohibition Act, 1961",
    "Maintenance and Welfare of Parents and Senior Citizens Act, 2007",
    "Family Courts Act, 1984",
    "Guardians and Wards Act, 1890",
    "Prohibition of Child Marriage Act, 2006",
    "Protection of Children from Sexual Offences Act, 2012",
    "Juvenile Justice (Care and Protection of Children) Act, 2015",
    "Representation of the People Act, 1951",
    "Legal Services Authorities Act, 1987",
    "Unlawful Activities (Prevention) Act, 1967",
    "Narcotic Drugs and Psychotropic Substances Act, 1985",
    "Prevention of Corruption Act, 1988",
    "Protection of Civil Rights Act, 1955",
    "Scheduled Castes and Scheduled Tribes (Prevention of Atrocities) Act, 1989",
    "Registration Act, 1908",
    "Land Acquisition Act, 2013",
    "Benami Transactions (Prohibition) Act, 1988",
    "Consumer Protection Act, 2019",
    "Environment (Protection) Act, 1986",
    "Air (Prevention and Control of Pollution) Act, 1981",
    "Water (Prevention and Control of Pollution) Act, 1974",
    "Motor Vehicles Act, 1988",
    "Information Technology Act, 2000",
    "Digital Personal Data Protection Act, 2023",
    "Right to Information Act, 2005"
]
final_acts=[]

# HTTP headers to mimic a real browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": "https://www.indiacode.nic.in/"
}

# ─── HELPERS ───────────────────────────────────────────────────────

def search_act(act_name: str):
    """Search IndiaCode for the act and return the detail-page URL of the first exact match."""
    print('hello')
    params = {
        "query": act_name,
        "filtername":"title",
        "filtertype":"contains",
        "filterquery":act_name,
        "sort_by":"dc.identifier.actno_sort",
        "order":"asc"
    }
    resp = requests.get(SEARCH_URL, params=params, headers=HEADERS, timeout=10)
    soup = BeautifulSoup(resp.text, "html.parser")
    table = soup.find("table", class_="table")
    if not table:
        return []
    acts = []
    
    for tr in table.find_all("tr"):
        td_name = tr.find("td", headers="t3")
        td_link = tr.find("td", headers="t4")
        if td_name and td_link:
            name = td_name.get_text(strip=False)
            a = td_link.find("a", href=True)
            if a:
                detail_url = urljoin(SEARCH_URL, a["href"])
                acts.append((name, detail_url))
            if(len(acts)>1):
                break
    print(acts)
    return acts

def fetch_detail_page(url: str) -> requests.Response:
    return requests.get(url, headers=headers,timeout=10)

def extract_pdf_link(html: str):
    soup = BeautifulSoup(html, "html.parser")
    main = soup.find("main", id="content")
    if not main:
        return None
    # first link ending in .pdf
    tag = main.find("a", href=lambda h: h and h.lower().endswith(".pdf"))
    return urljoin(SEARCH_URL, tag["href"]) if tag else None

def download_pdf(url: str, dest: Path):
    resp = requests.get(url, headers=headers,timeout=20)
    resp.raise_for_status()
    with open(dest, "wb") as f:
        f.write(resp.content)
# ─── MAIN WORKFLOW ─────────────────────────────────────────────────

# def main():
#     for act in ACT_NAMES:
#         wordList=act.split(" ")
#         wordList.pop()
        
#         lastWord=wordList[-1]
#         lastWord=lastWord[:-1]
#         wordList.pop()
#         wordList.append(lastWord)
#         safe_fname = "".join(c for c in " ".join(wordList) if c.isalnum() or c in " _-").strip() + ".pdf"
#         out_path = OUTPUT_DIR / safe_fname
#         if out_path.exists():
#             print(f"🔹 Already downloaded: {act}")
#             continue

#         print(f"⏳ Searching for: {act}")
#         acts = search_act(act)
        
#         if not acts:
#             print("No entries found, done.")
#             continue

#         for name, detail_url in acts:
#             wordList=name.split(" ")
#             wordList.pop()
#             lastWord=wordList[-1]
#             lastWord=lastWord[:-1]
#             wordList.pop()
#             wordList.append(lastWord)
#             # safe = "".join(c for c in name if c.isalnum() or c in " _-").strip()
#             temp = "".join(c for c in  " ".join(wordList) if c.isalnum() or c in " _-")
# # 2) Swap spaces for underscores
#             safe = temp.strip().replace(" ", "_")
            
#             pdf_path = OUTPUT_DIR / f"{safe}.pdf"
#             if pdf_path.exists():
#                 print(f"✔ Skipping (exists): {name}")
#                 continue
#             try:
#                 dresp = fetch_detail_page(detail_url)
#                 dresp.raise_for_status()
#                 pdf_link = extract_pdf_link(dresp.text)
#                 if not pdf_link:
#                     print(f"⚠️  No PDF found for: {name}")
#                     continue

#                 print(f"⬇️  Downloading '{name}'")
#                 download_pdf(pdf_link, pdf_path)
#                 process_and_embed(pdf_path,safe)
#                 # time.sleep(DELAY)
#             except requests.HTTPError as he:
#                 print(f"❌ HTTP error for '{name}': {he}")
#             except Exception as ex:
#                 print(f"❌ Unexpected error for '{name}': {ex}")

# if __name__ == "__main__":
#     main()

FAILED_DIR = Path("all_central_acts_pdfs")  

# # ─── EMBED LOOP ────────────────────────────────────────────────────

def embed_failed_pdfs(pdf_dir: Path):
    print("Looking in:", pdf_dir.resolve())
    pdf_paths = list(pdf_dir.glob("*.pdf"))
    if not pdf_paths:
        print("✅ No PDFs to embed.")
        return

    for pdf_path in pdf_paths:
        name = pdf_path.stem     # filename without .pdf
        print(f"🔄 Processing leftover PDF: {name}")
        try:
            process_and_embed(pdf_path, name)
            print(f"✔ Embedded and removed: {name}")
        except Exception as e:
            print(f"❌ Failed on {name}: {e}")

if __name__ == "__main__":

    ##################################################ADD THE INDEX
    query="i am being harrased by a loan agent"
    model=next(embedder_cycle)
    vectorstore = UpstashVectorStore(
      embedding=model,
      index_url=os.getenv("UPSTASH_VECTOR_REST_URL"),
      index_token=os.getenv("UPSTASH_VECTOR_REST_TOKEN"),
      index=index,
      )
    retriever=vectorstore.as_retriever(
    # search_type="similarity_score_threshold",
    # search_kwargs={'score_threshold': 0.}
)
    vectors = model.embed_query(query)
    
    op=retriever.invoke(query)
    op=vectorstore.similarity_search_by_vector(embedding=vectors)
    op=query_result = index.query(
    vector=vectors,
    include_metadata=True,
    include_data=False,
    include_vectors=False,
    top_k=4,
    )
    print(op)
    
    # embed_failed_pdfs(FAILED_DIR)
