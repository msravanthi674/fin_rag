from fastapi import APIRouter, UploadFile, File, Form
import os
from app.tasks import process_file_task
from app.services.claude_service import analyze_documents, generate_draft_email
from app.services.projection_service import projection_service

router = APIRouter()

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "data/uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/email-webhook")
async def receive_email(
    company: str = Form("Unknown"),
    files: list[UploadFile] = File(...)
):
    try:
        print(f"--- Received Deal Processing Request for: {company} ---")
        results = []
        contents = []

        for file in files:
            file_path = os.path.join(UPLOAD_DIR, file.filename)

            with open(file_path, "wb") as f:
                f.write(await file.read())

            result = process_file_task(
                file_path=file_path,
                file_name=file.filename,
                company=company
            )

            if result.get("status") == "success":
                contents.append(f"FILE: {file.filename}\nTYPE: {result.get('type')}\nCONTENT: {result.get('content')}")

            results.append({
                "file": file.filename,
                "result": result
            })

        # Logic for analysis and drafting
        analysis_text = "No content extracted to analyze."
        revenue_data = []
        draft_email = "No email drafted."

        if contents:
            print(f"Analyzing {len(contents)} document chunks...")
            try:
                analysis_data = analyze_documents(contents) or {}
                analysis_text = analysis_data.get("analysis_markdown", "No summary could be generated.")
                revenue_data = analysis_data.get("revenue_data", [])
                
                if revenue_data:
                    formatted_proj = [
                        {"metric": "Revenue", "value": str(r.get("revenue")), "period": str(r.get("year")), "source_context": "Extracted from uploaded documents."}
                        for r in revenue_data
                    ]
                    projection_service.save_projections(company, formatted_proj)
                    
                draft_email = generate_draft_email(analysis_text, company, revenue_data)
            except Exception as e:
                print(f"Analysis/Drafting Failed: {e}")
                analysis_text = f"AI Analysis failed: {str(e)}"
                draft_email = "Unable to generate draft due to AI error."

        return {
            "status": "processed",
            "results": results,
            "analysis": analysis_text,
            "revenue_data": revenue_data,
            "draft_email": draft_email
        }
    except Exception as e:
        print(f"GLOBAL WEBHOOK ERROR: {e}")
        return {
            "status": "error",
            "message": str(e),
            "analysis": "Internal Server Error occurred during processing.",
            "draft_email": "Error processing your request."
        }