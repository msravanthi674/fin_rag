from app.services.drive_service import find_or_create_folder, upload_file
from app.services.file_extractor import extract_text
from app.services.claude_service import structure_text
from app.services.rag_service import rag


def process_file_task(file_path, file_name, company):
    try:
        print("\n🚀 ===== TASK STARTED =====")
        print("📄 File:", file_name)

        # 1. Drive Upload
        folder_id = find_or_create_folder(company)
        drive_id = upload_file(file_path, folder_id)

        print("☁️ Uploaded:", drive_id)

        # 2. Extract
        text = extract_text(file_path)

        if not text.strip():
            return {"status": "empty"}

        # 3. Claude
        structured = structure_text(text)

        # 4. RAG
        rag.add_documents([{
            "text": structured.get("content", ""),
            "type": structured.get("type", "unknown"),
            "section": structured.get("section", "general")
        }])

        print("✅ Stored in RAG:", rag.index.ntotal)

        return {
            "status": "success",
            "file": file_name,
            "content": structured.get("content", ""),
            "type": structured.get("type", "unknown")
        }

    except Exception as e:
        print("❌ ERROR:", str(e))
        return {"status": "error", "error": str(e)}