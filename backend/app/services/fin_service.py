import yfinance as yf
import requests
import json
import numpy as np
from sec_edgar_downloader import Downloader
from bs4 import BeautifulSoup
import os
import re
from typing import List, Dict
from app.services.file_extractor import extract_text
from app.services.projection_service import projection_service


def chunk_text(text: str, max_len=500) -> List[str]:
    # Split by periods or newlines to handle paragraphs and CSV rows
    sentences = re.split(r'(?<=\.\s+)|(?<=\n)', text)
    chunks = []
    current = ''
    for sent in sentences:
        if len(current) + len(sent) < max_len:
            current += sent
        else:
            if current:
                chunks.append(current.strip())
            current = sent
    if current:
        chunks.append(current.strip())
    return chunks

def fetch_moneycontrol(symbol: str) -> List[Dict]:
    try:
# Moneycontrol US stocks - dynamic search
        url = f"https://www.moneycontrol.com/stocks/marketstats/nse/index.php"  # Use general or search page, scrape AAPL/MSFT etc.
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        if not response.ok:
            return []
        soup = BeautifulSoup(response.text, 'html.parser')
        # Simplified: look for AAPL mentions
        text = soup.get_text()[:2000]
        docs = [{"text": f"{symbol} Moneycontrol overview: {text}", "type": "moneycontrol", "symbol": symbol}]
        return docs
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        docs = []
        
        # Example selectors (inspect site for exact)
        title = soup.find('h1', class_='pc_lh25') or soup.title
        company_name = title.text.strip() if title else 'Unknown'
        
        # Financial ratios/metrics
        metrics = {}
        metric_tables = soup.find_all('div', class_='greybox')
        for table in metric_tables:
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                if len(cols) == 2:
                    key = cols[0].text.strip()
                    value = cols[1].text.strip()
                    metrics[key] = value
        
        text = f"{symbol} from Moneycontrol: {company_name}. Key Metrics: {json.dumps(metrics, indent=2)[:1000]}..."
        docs.append({"text": text, "type": "moneycontrol_metrics", "symbol": symbol})
        
        return docs
    except Exception as e:
        print(f"Moneycontrol scrape error for {symbol}: {e}")
        return []

def fetch_yfinance(symbol: str) -> List[Dict]:
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        financials = ticker.financials
        balance = ticker.balance_sheet
        cashflow = ticker.cashflow

        docs = []
        
        # Company info
        text = f"{symbol}: {info.get('longName', '')}. Sector: {info.get('sector', '')}. Industry: {info.get('industry', '')}. Market Cap: {info.get('marketCap', '')}."
        docs.append({"text": text, "type": "company_info", "symbol": symbol})
        
        # Financials
        for stmt_name, stmt in [("financials", financials), ("balance_sheet", balance), ("cashflow", cashflow)]:
            if stmt is not None and hasattr(stmt, 'empty') and not stmt.empty:
                stmt_str = stmt.to_string()
                chunks = chunk_text(stmt_str, max_len=400)
                for chunk in chunks:
                    docs.append({"text": chunk, "type": "financial_statement", "symbol": symbol, "statement": stmt_name})
            else:
                docs.append({"text": f"No {stmt_name} data for {symbol}", "type": "financial_missing", "symbol": symbol})
        return docs
    except Exception as e:
        print(f"yfinance error for {symbol}: {e}")
        return [{"text": f"yfinance error for {symbol}: {str(e)}", "type": "error_yf", "symbol": symbol}]
    
    return docs

def fetch_sec_filing(symbol: str, form: str = '10-K') -> List[Dict]:
    try:
        dl = Downloader("FinRAG", "contact@finrag.com", "./sec_filings")
        dl.get(form, symbol, limit=1)
        
        docs = []
        filing_dir = f"./sec_filings/{form}/{symbol}"
        if os.path.exists(filing_dir):
            for file in os.listdir(filing_dir):
                if file.endswith('.txt'):
                    path = os.path.join(filing_dir, file)
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        soup = BeautifulSoup(f.read(), 'html.parser')
                        text = soup.get_text()
                        chunks = chunk_text(text)
                        for chunk in chunks:
                            docs.append({"text": chunk, "type": "sec_filing", "symbol": symbol, "form": form, "file": file})
        return docs
    except Exception as e:
        print(f"SEC fetch error for {symbol}: {e}")
        return []

def fetch_local_yfinance_csv(symbol: str) -> List[Dict]:
    try:
        base_dir = "yfinance_data"
        symbol_dir = os.path.join(base_dir, symbol)
        docs = []
        
        if os.path.exists(symbol_dir):
            for file in os.listdir(symbol_dir):
                if file.endswith('.csv'):
                    path = os.path.join(symbol_dir, file)
                    text = extract_text(path)
                    chunks = chunk_text(text)
                    for chunk in chunks:
                        docs.append({
                            "text": chunk, 
                            "type": "local_yfinance_csv", 
                            "symbol": symbol, 
                            "filename": file
                        })
        return docs
    except Exception as e:
        print(f"Local yfinance CSV fetch error for {symbol}: {e}")
        return []

def ingest_fin_data(symbol: str) -> str:
    from app.services.rag_service import rag
    import requests  # Add for moneycontrol
    
    docs_yf = fetch_yfinance(symbol)
    docs_mc = fetch_moneycontrol(symbol)
    try:
        docs_sec = fetch_sec_filing(symbol)
    except Exception as e:
        print(f"SEC filing fetch error for {symbol}: {e}")
        docs_sec = []
    
    docs_local = fetch_local_yfinance_csv(symbol)
    docs = docs_yf + docs_mc + docs_sec + docs_local
    
    if docs:
        rag.add_documents(docs)
        
        # Extract projections from the newly ingested docs
        # We take a representative sample of text to stay within tokens
        full_context = "\n".join([d['text'] for d in docs[:20]]) # Take first 20 chunks
        projection_service.extract_projections(symbol, full_context)
        
        return f"Ingested {len(docs)} chunks and extracted financial projections for {symbol}"
    else:
        raise ValueError(f"No documents fetched for {symbol}")

