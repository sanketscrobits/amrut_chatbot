"""
Admin Router - Escalation management endpoints for admin panel.
"""
from fastapi import APIRouter, HTTPException, WebSocket
from src.utils.escalation_manager import (
    list_pending_escalations,
    list_active_escalations,
    accept_escalation,
    resolve_escalation,
    get_escalation,
    handle_websocket_chat,
    close_escalation_connections
)

admin_router = APIRouter(tags=["Admin"])


@admin_router.get("/admin/escalations/pending")
async def get_pending_escalations():
    """List all pending escalations for admin panel."""
    escalations = list_pending_escalations()
    return {"status": "ok", "escalations": escalations, "count": len(escalations)}


@admin_router.get("/admin/escalations/active")
async def get_active_escalations():
    """List all active escalations."""
    escalations = list_active_escalations()
    return {"status": "ok", "escalations": escalations, "count": len(escalations)}


@admin_router.patch("/admin/escalations/{escalation_id}/accept")
async def admin_accept_escalation(escalation_id: str):
    """Admin accepts an escalation to start chatting."""
    if accept_escalation(escalation_id):
        return {
            "status": "ok",
            "message": "Escalation accepted",
            "websocket_url": f"/ws/escalation/{escalation_id}/admin"
        }
    raise HTTPException(status_code=404, detail="Escalation not found or already accepted")


@admin_router.patch("/admin/escalations/{escalation_id}/resolve")
async def admin_resolve_escalation(escalation_id: str):
    """Mark escalation as resolved - removes from memory."""
    await close_escalation_connections(escalation_id)
    if resolve_escalation(escalation_id):
        return {"status": "ok", "message": "Escalation resolved and removed"}
    raise HTTPException(status_code=404, detail="Escalation not found")


# Admin WebSocket Endpoint for Escalation Chat
@admin_router.websocket("/ws/escalation/{escalation_id}/admin")
async def websocket_admin_chat(websocket: WebSocket, escalation_id: str):
    """
    WebSocket for admin real-time chat with user during escalation.
    """
    escalation = get_escalation(escalation_id)
    if not escalation:
        await websocket.close(code=4001)
        return
    
    await handle_websocket_chat(websocket, escalation_id, "admin")
