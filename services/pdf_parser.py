import fitz  # PyMuPDF
import re

def parse_and_clean_pdf(pdf_path: str) -> str:
    """
    Parses a PDF file using PyMuPDF and performs an extended set of cleaning steps to
    prepare input for an LLM (e.g., clause extraction). Add or remove steps as needed
    based on your specific document layout.
    """
    # 1. Open the PDF file
    doc = fitz.open(pdf_path)
    all_text = []

    # 2. Extract raw text from each page
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        page_text = page.get_text("text")
        all_text.append(page_text)
    doc.close()

    # 3. Combine pages into one big string
    combined_text = "\n".join(all_text)

    # -----------------------------------------------
    # 4. Base Cleaning (from earlier version)
    # -----------------------------------------------

    # 4.1 Remove non-printable/control characters
    combined_text = re.sub(r"[\x00-\x1F\x7F]", "", combined_text)
    print('removed non-printable')
    # 4.3 Normalize line breaks (3+ newlines → exactly 2)
    combined_text = re.sub(r"\n{3,}", "\n\n", combined_text)
    print('normalise line breaks')
    # 4.4 Strip leading/trailing whitespace from each line & drop empty lines
    lines = combined_text.split("\n")
    cleaned_lines = [line.strip() for line in lines if line.strip() != ""]
    combined_text = "\n".join(cleaned_lines)

    # -----------------------------------------------
    # 5. Additional Legal‐PDF–Specific Cleaning Steps
    # -----------------------------------------------

    # 5.1 Remove or normalize page numbers / footers that follow "Page X of Y" or "(X/Y)"
    #     Example patterns: "Page 3 of 10", "3/10", "––3––" (common in scanned footers)
    combined_text = re.sub(r"(?m)^\s*Page\s+\d+\s+of\s+\d+\s*$", "", combined_text)
    
    combined_text = re.sub(r"(?m)^\s*\(?\d+\s*/\s*\d+\)?\s*$", "", combined_text)
    
    combined_text = re.sub(r"(?m)^[—–\-]{1,}\s*\d+\s*[—–\-]{1,}$", "", combined_text)
    print('removing headers and footers')
    # 5.2 Fix hyphenation at line breaks (e.g., "repre-\nsentation" → "representation")
    #     Detect a hyphen at end-of-line followed by a newline and immediately continue text.
    # 5.3 Merge lines that were broken mid-sentence— 
    #     if a line doesn’t end in punctuation (.,;:?), assume it should continue.
    #     This prevents splitting a single sentence into two lines.
    merged_lines = []
    for line in combined_text.split("\n"):
        if merged_lines and not re.search(r"[\.!?;:]$", merged_lines[-1]):
            # If previous line did not end with punctuation, merge
            merged_lines[-1] += " " + line
        else:
            merged_lines.append(line)
    combined_text = "\n".join(merged_lines)

    # 5.4 Normalize quotation marks and apostrophes

    # 5.5 Remove or flag “Confidential” / “Attorney-Client Privilege” banners

    # 5.6 Strip out common “Table of Contents” headings or page-number TOC lines
    #     (e.g., “1. Introduction…… 1”, “2. Definitions…… 5”)
    combined_text = re.sub(r"(?m)^\d+\.\s+.+\.*\s+\d+\s*$", "", combined_text)

    # 5.7 Remove HTML-like artifacts, if any (e.g., “<u>Clause</u>” → “Clause”)
    combined_text = re.sub(r"<[^>]+>", "", combined_text)
    print('removed HTML')
    # 5.8 Remove stray footnote markers (e.g., “1)”, “[1]”, “(a)” at ends of lines)
    combined_text = re.sub(r"(?m)\s*\[\d+\]\s*$", "", combined_text)
    combined_text = re.sub(r"(?m)\s*\d+\)\s*$", "", combined_text)
    combined_text = re.sub(r"(?m)\s*\([a-zA-Z]\)\s*$", "", combined_text)
    print('again header adn footer')
    # 5.9 Standardize section/ clause numbering so an LLM sees “Section 1.1” clearly
    #     e.g., change “SECTION I. Overview” to “Section 1. Overview” (Roman→Arabic, if needed).
    #     This example only normalizes “SECTION I–X” → “Section 1–10” (basic)
    # roman_map = {
    #     "I": "1", "II": "2", "III": "3", "IV": "4", "V": "5",
    #     "VI": "6", "VII": "7", "VIII": "8", "IX": "9", "X": "10"
    # }
    # def replace_roman(match):
    #     roman = match.group(1)
    #     arabic = roman_map.get(roman.upper(), roman)
    #     return f"Section {arabic}"
    # combined_text = re.sub(r"SECTION\s+(I|II|III|IV|V|VI|VII|VIII|IX|X)(?=\b)", replace_roman, combined_text, flags=re.IGNORECASE)

    # 5.10 Collapse multiple blank lines again (in case previous steps introduced new gaps)
    # combined_text = re.sub(r"\n{3,}", "\n\n", combined_text)

    # -----------------------------------------------
    # 6. Return fully cleaned text
    # -----------------------------------------------
    return combined_text
