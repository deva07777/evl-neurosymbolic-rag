"""Document processing: loading, smart chunking, OCR table extraction, cleaning."""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import re
import logging
from pathlib import Path
from config import config
from utils import logger, timeit, FinChatError

try:
    import pdfplumber
except Exception:
    pdfplumber = None
    logger.warning("pdfplumber not installed - PDF parsing may fail")

try:
    import pytesseract
    from PIL import Image
except Exception:
    pytesseract = None

@dataclass
class DocumentChunk:
    id: str
    text: str
    page_num: Optional[int]
    section_type: Optional[str]
    company: Optional[str]
    date: Optional[str]
    metadata: Dict[str, Any]


@timeit
def clean_and_normalize_text(text: str) -> str:
    """Clean OCR artifacts, normalize currencies and dates.

    - Remove repeated headers/footers heuristically
    - Normalize INR/US$ symbols
    - Normalize newlines and spaces
    """
    if not text:
        return ""
    # remove multiple newlines
    text = re.sub(r"\r\n|\r", "\n", text)
    # remove repeated page footers like 'Page X of Y' or page numbers
    text = re.sub(r'Page\s+\d+\s+of\s+\d+', '', text, flags=re.I)
    text = re.sub(r'\n{3,}', '\n\n', text)
    # normalize currency symbols
    text = text.replace('₹', 'INR ').replace('Rs.', 'INR ').replace('$', 'USD ')
    # normalize dates like 31-03-2020 to 2020-03-31 (DD-MM-YYYY to YYYY-MM-DD)
    text = re.sub(r"\b(\d{1,2})[\-/](\d{1,2})[\-/](\d{4})\b", lambda m: f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}", text)
    # remove OCR noise
    text = re.sub(r"[^\S\n]{2,}", " ", text)
    return text.strip()


@timeit
def load_and_chunk_documents(file_path: str, strategy: str = "smart") -> List[DocumentChunk]:
    """Load a PDF/text and chunk smartly keeping headings/tables together.

    Returns list of DocumentChunk.
    """
    p = Path(file_path)
    if not p.exists():
        raise FinChatError("file not found: %s" % file_path)

    raw_text_pages: List[str] = []
    if p.suffix.lower() == '.pdf':
        if not pdfplumber:
            raise FinChatError("pdfplumber required to parse PDFs")
        with pdfplumber.open(str(p)) as pdf:
            for page in pdf.pages:
                try:
                    raw_text_pages.append(page.extract_text() or "")
                except Exception:
                    raw_text_pages.append("")
    else:
        raw_text_pages = [p.read_text(encoding='utf-8')]

    # Merge and clean
    cleaned_pages = [clean_and_normalize_text(t) for t in raw_text_pages]
    # naive heading detection: lines in ALL CAPS or starting with numbers
    chunks: List[DocumentChunk] = []
    chunk_size = config.CHUNK_SIZE
    overlap = config.CHUNK_OVERLAP
    id_counter = 0
    for page_idx, page_text in enumerate(cleaned_pages, start=1):
        # split by headings to preserve sections
        sections = re.split(r"\n(?=[A-Z][A-Z\s]{10,}\n)", page_text)
        for sec in sections:
            sec = sec.strip()
            if not sec:
                continue
            # chunk this section by characters but try to keep sentences
            start = 0
            L = len(sec)
            while start < L:
                end = min(start + chunk_size, L)
                chunk_text = sec[start:end]
                # backtrack to nearest sentence end
                if end < L:
                    m = re.search(r"([\.\n]\s)[^\.]*$", chunk_text)
                    if m:
                        cut = m.start()+1
                        if cut > 200:
                            end = start + cut
                            chunk_text = sec[start:end]
                chunk_text = chunk_text.strip()
                if not chunk_text:
                    break
                id_counter += 1
                chunks.append(DocumentChunk(
                    id=f"chunk_{page_idx}_{id_counter}",
                    text=chunk_text,
                    page_num=page_idx,
                    section_type=None,
                    company=None,
                    date=None,
                    metadata={"source": str(p)}
                ))
                start = end - overlap
    return chunks


@timeit
def extract_financial_tables(file_path: str) -> List[Dict[str, Any]]:
    """Extract tables from PDFs using pdfplumber and OCR fallback.

    Returns a list of structured table dicts with tags.
    """
    p = Path(file_path)
    if not p.exists():
        raise FinChatError("file not found: %s" % file_path)
    tables = []
    if p.suffix.lower() != '.pdf':
        return tables
    if not pdfplumber:
        return tables
    with pdfplumber.open(str(p)) as pdf:
        for page in pdf.pages:
            try:
                page_tables = page.extract_tables()
                for t in page_tables:
                    # convert to rows
                    rows = [list(map(lambda x: (x or '').strip(), r)) for r in t]
                    tables.append({
                        'page': page.page_number,
                        'rows': rows,
                        'tag': guess_table_tag(rows)
                    })
            except Exception:
                continue
    return tables


def guess_table_tag(rows: List[List[str]]) -> str:
    """Heuristic tag for table type based on header keywords."""
    header = ' '.join(rows[0]).lower() if rows and rows[0] else ''
    if any(k in header for k in ('balance', 'assets', 'liabilities')):
        return 'balance_sheet'
    if any(k in header for k in ('revenue', 'sales', 'turnover')):
        return 'income_statement'
    if any(k in header for k in ('cash', 'cash flow')):
        return 'cash_flow'
    return 'table'
