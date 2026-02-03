from fastapi import FastAPI, UploadFile, File, HTTPException, WebSocket
import logging
import os
import sys
import shutil
import tempfile
from pathlib import Path

# Add project root to sys path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from settings import NAMESPACE
from src.Uploader.uploader_pinecone import MyDocumentUploader
from src.utils.escalation_manager import (
    list_pending_escalations,
    list_active_escalations,
    accept_escalation,
    resolve_escalation,
    get_escalation,
    handle_websocket_chat,
    close_escalation_connections
)

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.post("/upload/{uuid}")
async def upload_document(uuid: str, file: UploadFile = File(...)):
    """
    Upload and ingest a document file using the provided UUID as source.
    The content is uploaded to the namespace defined in settings.NAMESPACE.
    """
    try:
        if not NAMESPACE:
            raise HTTPException(status_code=500, detail="NAMESPACE not configured in settings.")

        suffix = os.path.splitext(file.filename)[1]
        
        # Save uploaded file to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
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


# =============================================================================
# Admin Escalation Management Endpoints
# =============================================================================

@app.get("/admin/escalations/pending")
async def get_pending_escalations():
    """List all pending escalations for admin panel."""
    escalations = list_pending_escalations()
    return {"status": "ok", "escalations": escalations, "count": len(escalations)}


@app.get("/admin/escalations/active")
async def get_active_escalations():
    """List all active escalations."""
    escalations = list_active_escalations()
    return {"status": "ok", "escalations": escalations, "count": len(escalations)}


@app.patch("/admin/escalations/{escalation_id}/accept")
async def admin_accept_escalation(escalation_id: str):
    """Admin accepts an escalation to start chatting."""
    if accept_escalation(escalation_id):
        return {
            "status": "ok",
            "message": "Escalation accepted",
            "websocket_url": f"/ws/escalation/{escalation_id}/admin"
        }
    raise HTTPException(status_code=404, detail="Escalation not found or already accepted")


@app.patch("/admin/escalations/{escalation_id}/resolve")
async def admin_resolve_escalation(escalation_id: str):
    """Mark escalation as resolved - removes from memory."""
    await close_escalation_connections(escalation_id)
    if resolve_escalation(escalation_id):
        return {"status": "ok", "message": "Escalation resolved and removed"}
    raise HTTPException(status_code=404, detail="Escalation not found")


# Admin WebSocket Endpoint for Escalation Chat
@app.websocket("/ws/escalation/{escalation_id}/admin")
async def websocket_admin_chat(websocket: WebSocket, escalation_id: str):
    """
    WebSocket for admin real-time chat with user during escalation.
    """
    escalation = get_escalation(escalation_id)
    if not escalation:
        await websocket.close(code=4001)
        return
    
    await handle_websocket_chat(websocket, escalation_id, "admin")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010)