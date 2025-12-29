"""Document fetching and validation.

- SEC fetching via secedgar (with retries and robust parsing)
- Indian MCA annual report fetching (known company patterns, web scraping, validation)
- Caching to local filesystem with metadata tracking
- Completeness validation and issue detection
"""
from typing import Optional, Dict, Any, List
import os
import hashlib
from datetime import datetime
from pathlib import Path
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import re

from utils import ensure_dir, logger, FinChatError, save_json
from config import config

CACHE_DIR = Path(config.DATA_DIR) / "raw"
ensure_dir(str(CACHE_DIR))

_session: Optional[requests.Session] = None

def _get_session() -> requests.Session:
    """Get persistent requests session with retry logic."""
    global _session
    if _session is None:
        s = requests.Session()
        retries = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        s.mount('https://', HTTPAdapter(max_retries=retries))
        s.mount('http://', HTTPAdapter(max_retries=retries))
        _session = s
    return _session


try:
    from sec_edgar_downloader import Downloader
    SECEDGAR_AVAILABLE = True
except Exception:
    SECEDGAR_AVAILABLE = False
    logger.warning("sec-edgar-downloader not available; SEC download functions will raise explicit error")


def _cache_path_for(identifier: str, ext: str = "pdf") -> Path:
    """Generate deterministic cache path from identifier."""
    h = hashlib.sha256(identifier.encode('utf-8')).hexdigest()
    return CACHE_DIR / f"{h}.{ext}"


def _find_latest_file(directory: Path, patterns: List[str]) -> Optional[Path]:
    """Find latest file matching any glob pattern in directory."""
    files = []
    for p in patterns:
        files.extend(directory.rglob(p))
    if not files:
        return None
    files = sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)
    return files[0]


def _extract_text_from_html(path: Path) -> str:
    """Extract clean text from HTML file, removing scripts and noise."""
    try:
        html = path.read_text(encoding='utf-8', errors='ignore')
        soup = BeautifulSoup(html, 'lxml')
        for s in soup(['script', 'style']):
            s.decompose()
        text = soup.get_text(separator='\n')
        return re.sub(r"\n{2,}", "\n\n", text).strip()
    except Exception:
        logger.exception("Failed to parse HTML %s", path)
        return ''


def fetch_sec_filing(ticker: str, filing_type: str = "10-K") -> Path:
    """Fetch SEC filing for `ticker` and `filing_type`.

    Uses `secedgar` to download filings from SEC Edgar with retry logic.
    Validates completeness (presence of key sections). Caches locally.
    
    Args:
        ticker: Company ticker (e.g., "AAPL", "MSFT")
        filing_type: Type of filing (10-K, 10-Q, 8-K)
    
    Returns:
        Path to cached filing (HTML or text format)
    
    Raises:
        FinChatError: If secedgar unavailable or download fails
    """
    filing_type = filing_type.upper()
    identifier = f"SEC::{ticker}::{filing_type}"
    dest = _cache_path_for(identifier, "html")
    if dest.exists():
        logger.info("Using cached SEC filing: %s", dest)
        return dest

    if not SECEDGAR_AVAILABLE:
        raise FinChatError("secedgar package not available; install via: pip install sec-edgar-downloader")

    try:
        logger.info("Downloading %s %s from SEC via sec-edgar-downloader", ticker, filing_type)
        dl_dir = CACHE_DIR / f"sec_edgar_{ticker}_{filing_type}"
        ensure_dir(str(dl_dir))
        
        # Download using sec-edgar-downloader
        # Downloader requires company_name and email_address
        downloader = Downloader(company_name=ticker, email_address="bot@finchat.local", download_folder=str(dl_dir))
        downloader.get(form=filing_type, ticker_or_cik=ticker, include_amends=False, limit=1)
        
        # Find the latest downloaded file (may be html, htm, or txt)
        found = _find_latest_file(dl_dir, ['*.html', '*.htm', '*.txt', '*.pdf'])
        if not found:
            raise FinChatError(f"sec-edgar-downloader did not produce a filing for {ticker} {filing_type}")
        
        # Copy to stable cache path
        dest.write_text(found.read_text(encoding='utf-8', errors='ignore'))
        
        # Validate completeness
        text = _extract_text_from_html(dest)
        issues = []
        if filing_type == '10-K' and not re.search(r'Item\s+7\.|Management.?s Discussion', text, re.I):
            issues.append('Missing Item 7 / MD&A in downloaded 10-K')
        if len(text) < 1000:
            issues.append('Downloaded content appears too small (<1000 chars)')
        
        # Save metadata
        meta = {
            'path': str(dest),
            'ticker': ticker,
            'filing_type': filing_type,
            'downloaded_from': 'secedgar',
            'text_length': len(text),
            'issues': issues,
            'fetched_at': datetime.utcnow().isoformat()
        }
        save_json(meta, str(dest) + '.meta.json')
        
        if issues:
            logger.warning("Downloaded filing has warnings: %s", issues)
        return dest
        
    except Exception as e:
        logger.exception("SEC download failed for %s %s", ticker, filing_type)
        raise FinChatError(str(e))


# Known company investor URLs for efficient lookup
_KNOWN_COMPANY_PATTERNS = {
    'RELIANCE': [
        'https://www.relianceindustries.com/investors/annual-report/',
    ],
    'TCS': [
        'https://www.tcs.com/investor-relations/financial-statements',
        'https://www.tcs.com/investor-relations/annual-reports'
    ],
    'INFY': [
        'https://www.infosys.com/investors/reports-filings/annual-report.html'
    ],
    'HDFC': [
        'https://www.hdfcbank.com/about-us/investor-relations/annual-reports'
    ],
    'ASIANPAINT': [
        'https://www.asianpaints.com/investor-relations/annual-report.html'
    ]
}


def fetch_indian_annual_report(cin: str, company_name: str) -> Path:
    """Fetch Indian annual report by CIN or company name.

    Strategy:
      1. Check known company patterns first (Reliance, TCS, Infosys, HDFC, Asian Paints)
      2. Probe candidate investor-relations URLs
      3. Search for PDF links with 'annual' in href or text
      4. Download and validate PDF integrity
      5. Cache with metadata
    
    Args:
        cin: Corporate Identification Number
        company_name: Company name (e.g., "RELIANCE", "TCS")
    
    Returns:
        Path to cached PDF
    
    Raises:
        FinChatError: If unable to download after all strategies exhausted
    """
    identifier = f"MCA::{cin}::{company_name}"
    dest = _cache_path_for(identifier, "pdf")
    if dest.exists():
        logger.info("Using cached MCA doc: %s", dest)
        return dest

    session = _get_session()
    candidates = []
    n = company_name.strip().upper()
    
    # Add known patterns for this company
    if n in _KNOWN_COMPANY_PATTERNS:
        candidates.extend(_KNOWN_COMPANY_PATTERNS[n])
    
    # Add candidate patterns
    base = company_name.lower().replace(' ', '')
    candidates.extend([
        f'https://www.{base}.com/investors/annual-reports',
        f'https://www.{base}.com/investor/annual-report',
        f'https://www.{base}.com/investors',
        f'https://www.{base}.com/investor-relations'
    ])

    headers = {'User-Agent': 'FinChatBot/1.0 (+https://example.com/finchat)'}
    
    for url in candidates:
        try:
            logger.info('Probing %s for annual reports', url)
            r = session.get(url, headers=headers, timeout=10)
            if r.status_code != 200:
                continue
            
            soup = BeautifulSoup(r.text, 'lxml')
            
            # Find PDF links that reference 'annual' or 'report'
            links = []
            for a in soup.find_all('a', href=True):
                href = a['href']
                text = (a.get_text() or '').lower()
                if '.pdf' in href.lower() and ('annual' in href.lower() or 'annual' in text or 'report' in text):
                    links.append(href)
            
            # Fallback: grab all PDFs if no 'annual' match
            if not links:
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    if href.lower().endswith('.pdf'):
                        links.append(href)
            
            if not links:
                continue
            
            # Try first PDF link
            pdf_url = links[0]
            if not pdf_url.startswith('http'):
                from urllib.parse import urljoin
                pdf_url = urljoin(url, pdf_url)
            
            logger.info('Found PDF candidate: %s', pdf_url)
            pr = session.get(pdf_url, headers=headers, timeout=20)
            
            if pr.status_code == 200 and len(pr.content) > 1024:
                dest.write_bytes(pr.content)
                
                # Validate PDF
                pages = None
                try:
                    from PyPDF2 import PdfReader
                    r = PdfReader(str(dest))
                    pages = len(r.pages)
                except Exception:
                    pass
                
                # Save metadata
                meta = {
                    'path': str(dest),
                    'cin': cin,
                    'company': company_name,
                    'source': pdf_url,
                    'pages': pages,
                    'file_size': len(pr.content),
                    'fetched_at': datetime.utcnow().isoformat()
                }
                save_json(meta, str(dest) + '.meta.json')
                logger.info('Successfully downloaded MCA report for %s (%d pages)', company_name, pages or 0)
                return dest
                
        except Exception:
            logger.debug('Failed to probe %s', url, exc_info=True)

    raise FinChatError(
        f'Unable to automatically download MCA report for {company_name} (CIN: {cin}). '
        'Please provide the PDF manually or configure a data provider.'
    )


def validate_document(file_path: str) -> Dict[str, Any]:
    """Validate a document file and return comprehensive metadata.

    Performs checks on:
      - File existence and size
      - PDF structure and page count
      - Text extraction and content quality
      - Presence of key financial sections (heuristic)
    
    Returns:
        Dict with keys: path, size, format, pages, text_snippet, 
                        completeness_score (0.0-1.0), issues (list)
    
    Raises:
        FinChatError: If file not found
    """
    p = Path(file_path)
    if not p.exists():
        raise FinChatError(f"File not found: {file_path}")
    
    size = p.stat().st_size
    ext = p.suffix.lower()
    metadata: Dict[str, Any] = {"path": str(p), "size": size, "format": ext}
    issues: List[str] = []
    text = ''
    pages = None
    
    try:
        if ext == '.pdf':
            from PyPDF2 import PdfReader
            r = PdfReader(str(p))
            pages = len(r.pages)
            
            # Extract text from first 2 pages
            texts = []
            for i, pg in enumerate(r.pages[:2]):
                try:
                    texts.append(pg.extract_text() or '')
                except Exception:
                    texts.append('')
            text = '\n'.join(texts)
            
        elif ext in ('.html', '.htm', '.txt'):
            text = p.read_text(encoding='utf-8', errors='ignore')
        else:
            text = ''
            issues.append(f'Unsupported format: {ext}')
            
    except Exception as e:
        logger.debug('validate_document read error', exc_info=True)
        issues.append(f'Failed to read file: {str(e)}')

    metadata['pages'] = pages
    metadata['text_snippet'] = (text or '')[:1000]
    
    # Compute completeness score
    score = 1.0
    if size < 2000:
        issues.append('File too small (<2KB)')
        score -= 0.6
    if not text or len(text) < 500:
        issues.append('Insufficient text extracted')
        score -= 0.3
    
    # Look for common SEC/financial markers
    if re.search(
        r'Item\s+7\.|Management.?s Discussion|Balance Sheet|Consolidated Statement|'
        r'Income Statement|Cash Flow',
        (text or ''), re.I
    ):
        score += 0.2
    else:
        issues.append('Did not detect key financial sections')
        score -= 0.2

    metadata['completeness_score'] = max(0.0, min(1.0, round(score, 2)))
    metadata['issues'] = issues
    
    return metadata
