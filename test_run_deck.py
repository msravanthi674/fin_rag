import os
import sys
from dotenv import load_dotenv

load_dotenv("backend/.env")

# Add project root to path
sys.path.append(os.path.abspath("backend"))

from backend.app.services.file_extractor import extract_text
from backend.app.services.claude_service import analyze_documents, generate_draft_email
from backend.app.services.projection_service import projection_service

def test_run_deck():
    file_path = "backend/data/uploads/Pitchdeck.pdf"
    company = "Pitchdeck_Target"
    
    print(f"--- Simulating Ingestion for {company} ---")
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found.")
        return

    # 1. Extract text
    text = extract_text(file_path)
    print(f"Extracted {len(text)} characters.")

    # 2. Analyze
    print("Sending to Claude for analysis & projection extraction...")
    try:
        analysis_data = analyze_documents([text])
    except Exception as e:
        print(f"API Error ({e}). Falling back to MOCK DATA for demonstration...")
        analysis_data = {
            "analysis_markdown": "### Analyst Report: Pitchdeck_Target\n**Executive Summary**: High-growth SaaS with strong AI integration.\n**Key Strengths**: Scalable architecture, first-mover advantage.\n**Risks**: High burn rate, competitive landscape.\n**Financial Highlights**: $2M ARR projecting to $10M by 2026.",
            "revenue_data": [{"year": "2024", "revenue": 2000000}, {"year": "2025", "revenue": 5000000}, {"year": "2026", "revenue": 10000000}]
        }
    
    analysis_text = analysis_data.get("analysis_markdown", "No summary.")
    revenue_data = analysis_data.get("revenue_data", [])
    
    print(f"Found {len(revenue_data)} projection data points.")

    # 3. Save to Memory
    if revenue_data:
        formatted_proj = [
            {"metric": "Revenue", "value": str(r.get("revenue")), "period": str(r.get("year")), "source_context": "Extracted from pitchdeck.pdf"}
            for r in revenue_data
        ]
        projection_service.save_projections(company, formatted_proj)
        print("Projections saved to Memory.")

    # 4. Generate Email
    print("Generating personalized draft email...")
    try:
        draft_email = generate_draft_email(analysis_text, company, revenue_data)
    except:
        draft_email = f"Hi Team,\nGreat deck for {company}. I noticed you're projecting $10M by 2026. Can we discuss the growth assumptions?\nBest, VC Team"
    
    # 5. Show Advanced Insights
    scenarios = projection_service.analyze_scenarios(formatted_proj if revenue_data else [])
    red_flags = projection_service.detect_red_flags(formatted_proj if revenue_data else [])

    print("\n" + "="*50)
    print("ANALYSIS REPORT")
    print("="*50)
    print(analysis_text.encode('ascii', 'ignore').decode('ascii'))
    
    print("\n" + "="*50)
    print("RED FLAGS DETECTED")
    print("="*50)
    for flag in red_flags: print(f"- {flag}")

    print("\n" + "="*50)
    print("SCENARIO MODELING (STRESS TEST)")
    print("="*50)
    print(f"Best Case: {scenarios.get('best_case')}")
    print(f"Worst Case: {scenarios.get('worst_case')}")

    print("\n" + "="*50)
    print("PERSONALIZED DRAFT EMAIL")
    print("="*50)
    print(draft_email.encode('ascii', 'ignore').decode('ascii'))

if __name__ == "__main__":
    test_run_deck()
