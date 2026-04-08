from fastapi import APIRouter, Query
from app.services.rag_service import rag
from app.services.claude_service import client
from app.services.projection_service import projection_service
from app.services.benchmark_service import get_sector_benchmarks
import json
import os

router = APIRouter()


@router.get("/query")
def query_rag(
    q: str = Query(..., description="Query text"),
    symbol: str = Query(None, description="Optional stock symbol to filter")
):
    results = rag.query(q, k=10)
    if not results:
        return {"results": [], "message": "No data yet"}

    # Filter by symbol if provided
    filtered = [r for r in results if not symbol or r.get('symbol') == symbol]
    if not filtered:
        return {"results": [], "message": f"No data for symbol {symbol}"}

    # Context from top 5
    context = "\n\n".join(r["text"] for r in filtered[:5])

    # Fetch any known projections for this symbol
    projections = projection_service.get_projections(symbol) if symbol else []
    proj_context = ""
    scenarios = {}
    red_flags = []
    benchmarks = {}

    if symbol:
        benchmarks = get_sector_benchmarks(symbol)

    if projections:
        proj_context = "Known Financial Projections:\n" + "\n".join([
            f"- {p['metric']} for {p['period']}: {p['value']} (Source: {p.get('source_context', 'N/A')})"
            for p in projections
        ])
        scenarios = projection_service.analyze_scenarios(projections)
        red_flags = projection_service.detect_red_flags(projections)

    # Claude analysis
    prompt = f"""
    Analyze this financial data context for the query: "{q}"

    Context:
    {context}

    {proj_context}

    Provide a concise financial insight, key metrics, summary. Focus on revenue, growth, valuation if relevant.
    If projections are available, prioritize discussing them as they represent the future outlook.
    """
    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        analysis = response.content[0].text
    except Exception as e:
        analysis = f"Analysis error: {str(e)}"

    return {
        "results": filtered[:5],
        "analysis": analysis,
        "total": len(filtered),
        "projections": projections,
        "scenarios": scenarios,
        "red_flags": red_flags,
        "benchmarks": benchmarks
    }

@router.get("/projections")
def get_projections(symbol: str = Query(..., description="Stock symbol")):
    projections = projection_service.get_projections(symbol)
    return {"symbol": symbol, "projections": projections}
