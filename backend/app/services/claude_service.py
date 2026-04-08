from anthropic import Anthropic
import json
import os

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
DEFAULT_MODEL = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20240620")

def structure_text(text: str):
    prompt = f"""
    Extract structured information from this text.

    Return JSON with:
    - type (pitch / nda / financial / teaser / email)
    - section (revenue, growth, problem, etc.)
    - content (cleaned summary)

    Text:
    {text}
    """

    response = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )

    try:
        return json.loads(response.content[0].text)
    except:
        return {
            "type": "unknown",
            "section": "general",
            "content": text
        }

def analyze_documents(docs_context: list[str]):
    """Summarizes and analyzes multiple documents for a cohesive overview."""
    combined_text = "\n\n--- DOCUMENT BORDER ---\n\n".join(docs_context)
    
    prompt = f"""
    You are an expert venture capital analyst. Analyze the following documents (pitch deck, financial models, etc.) for a startup.
    
    IMPORTANT: Provide your output in a JSON format with exactly two keys:
    1. 'analysis_markdown': A comprehensive analysis including Executive Summary, Key Strengths, Risks, Financial Highlights (in Markdown).
    2. 'revenue_data': A list of objects with 'year' and 'revenue' keys (if found, otherwise an empty list). Try to extract historical or projected revenue if possible. Example: [{{"year": "2021", "revenue": 1000000}}, ...]

    Documents Context:
    {combined_text}
    """

    response = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )
    
    try:
        data = json.loads(response.content[0].text)
        return data
    except:
        return {
            "analysis_markdown": response.content[0].text,
            "revenue_data": []
        }

def generate_draft_email(analysis_summary: str, company: str, revenue_data: list = None):
    """Generates a professional email draft based on the document analysis and financial projections."""
    
    proj_str = ""
    if revenue_data:
        proj_str = "\nExtracted Projections:\n" + "\n".join([f"- {r.get('year')}: {r.get('revenue')}" for r in revenue_data])

    prompt = f"""
    Based on the following analysis of {company}'s pitch deck and documents, draft a professional and detailed email response.
    The email should:
    - Thank them for the revert and the materials.
    - Mention specific financial highlights or projections (especially those listed below).
    - Show we've deep-dived into their revenue numbers and growth trajectory.
    - Ask 2-3 specific clarifying questions based on the risks or gaps identified.
    - Propose a follow-up call if the analysis is positive.
    - Maintain a professional, interested, yet critical venture capital tone.

    Analysis context:
    {analysis_summary}

    {proj_str}
    """

    response = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.content[0].text