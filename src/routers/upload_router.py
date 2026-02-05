"""
Upload Router - Document upload endpoints.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
import logging
import os
import tempfile

from settings import NAMESPACE
from src.Uploader.uploader_pinecone import MyDocumentUploader

logger = logging.getLogger(__name__)

upload_router = APIRouter(tags=["Upload"])

# File upload validation constants
ALLOWED_EXTENSIONS = {'.md', '.pdf', '.txt', '.doc', '.docx', '.csv', '.json'}
MAX_FILE_SIZE = 10_000_000  # 10MB


@upload_router.post("/upload/{uuid}")
async def upload_document(uuid: str, file: UploadFile = File(...)):
    """
    Upload and ingest a document file using the provided UUID as source.
    The content is uploaded to the namespace defined in settings.NAMESPACE.
    """
    try:
        if not NAMESPACE:
            raise HTTPException(status_code=500, detail="NAMESPACE not configured in settings.")

        # Validate file extension
        suffix = os.path.splitext(file.filename)[1].lower()
        if suffix not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type '{suffix}'. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # Read file content for validation
        content = await file.read()
        
        # Validate file size
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large ({len(content)} bytes). Maximum size: {MAX_FILE_SIZE} bytes (10MB)"
            )
        
        # Validate content is not empty
        if len(content) == 0:
            raise HTTPException(
                status_code=400,
                detail="File is empty. Please upload a file with content."
            )
        
        # Save uploaded file to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            # Init uploader
            uploader = MyDocumentUploader()
            
            # Upload
            success = uploader.upload_document(
                file_path=tmp_path,
                uuid=uuid,
                namespace=NAMESPACE
            )
            
            if not success:
                raise HTTPException(status_code=400, detail="Failed to extract content from file.")
            
            logger.info(f"Document {file.filename} ingested with Source ID: {uuid} into Namespace: {NAMESPACE}")
            
        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

        return {
            "status": "ok", 
            "message": f"Document ingested successfully.",
            "source_id": uuid,
            "namespace": NAMESPACE
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in /upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))
