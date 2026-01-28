from fastapi import FastAPI
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.Uploader.uploader_pinecone import MyDocumentUploader

app = FastAPI()

@app.post("/upload")
def upload():
    """Upload documents to Pinecone."""
    try:
        uploader = MyDocumentUploader()
        uploader.upload_documents()
        return {"message": "Upload completed"}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010)