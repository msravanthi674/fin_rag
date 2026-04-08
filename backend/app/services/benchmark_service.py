import yfinance as yf
from typing import Dict, List

def get_sector_benchmarks(symbol: str) -> Dict:
    """Fetches public market benchmarks for the company's sector."""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        sector = info.get('sector')
        industry = info.get('industry')
        
        if not sector:
            return {"error": "Sector not found"}

        # Basic sector mapping for common benchmarks (simplified)
        # In a real app, this would query a structured DB of sector averages
        benchmarks = {
            "Technology": {"avg_margin": "25-35%", "revenue_multiple": "6-10x", "growth_benchmark": "20%+"},
            "Financial Services": {"avg_margin": "20-30%", "revenue_multiple": "2-4x", "growth_benchmark": "10%+"},
            "Healthcare": {"avg_margin": "15-25%", "revenue_multiple": "4-8x", "growth_benchmark": "15%+"},
            "Consumer Cyclical": {"avg_margin": "10-20%", "revenue_multiple": "1-3x", "growth_benchmark": "8%+"}
        }
        
        return {
            "symbol": symbol,
            "sector": sector,
            "industry": industry,
            "benchmarks": benchmarks.get(sector, {"avg_margin": "N/A", "revenue_multiple": "N/A", "growth_benchmark": "N/A"})
        }
    except Exception as e:
        return {"error": str(e)}
