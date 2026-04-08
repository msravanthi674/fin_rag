import os
from app.services.claude_service import structure_text

def load_documents(folder_path="data/documents"):
    docs = []

    for file in os.listdir(folder_path):
        with open(os.path.join(folder_path, file), "r", encoding="utf-8") as f:
            raw_text = f.read()

            structured = structure_text(raw_text)

            docs.append({
                "text": structured["content"],
                "type": structured["type"],
                "section": structured["section"]
            })

    return docs