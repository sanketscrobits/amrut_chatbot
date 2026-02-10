
"""
Escalation Manager - In-memory escalation management for user-to-admin chat.
No database storage - escalations are removed when resolved.
"""
import logging
import uuid
from datetime import datetime
from typing import Dict, Optional
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

# In-memory escalation storage: {escalation_id: escalation_data}
pending_escalations: Dict[str, dict] = {}

# Active WebSocket connections: {escalation_id: {"user": ws, "admin": ws}}
active_connections: Dict[str, Dict[str, WebSocket]] = {}


def create_escalation(user_question: str, context: Optional[str] = None) -> dict:
    """Create a new escalation and return its data."""
    escalation_id = str(uuid.uuid4())
    escalation = {
        "escalation_id": escalation_id,
        "user_question": user_question,
        "context": context,
        "status": "pending",  # pending -> active -> resolved
        "created_at": datetime.utcnow().isoformat()
    }
    pending_escalations[escalation_id] = escalation
    logger.info(f"Escalation created: {escalation_id}")
    return escalation


def get_escalation(escalation_id: str) -> Optional[dict]:
    """Get escalation by ID."""
    return pending_escalations.get(escalation_id)


def list_pending_escalations() -> list:
    """List all pending escalations for admin panel."""
    return [e for e in pending_escalations.values() if e["status"] == "pending"]


def list_active_escalations() -> list:
    """List all active escalations."""
    return [e for e in pending_escalations.values() if e["status"] == "active"]


def accept_escalation(escalation_id: str) -> bool:
    """Admin accepts an escalation."""
    if escalation_id in pending_escalations:
        pending_escalations[escalation_id]["status"] = "active"
        logger.info(f"Escalation accepted: {escalation_id}")
        return True
    return False


def resolve_escalation(escalation_id: str) -> bool:
    """Mark escalation as resolved and remove from memory."""
    if escalation_id in pending_escalations:
        del pending_escalations[escalation_id]
        logger.info(f"Escalation resolved and removed: {escalation_id}")
        return True
    return False


def get_active_connections() -> Dict[str, Dict[str, WebSocket]]:
    """Get active WebSocket connections."""
    return active_connections


async def handle_websocket_chat(websocket: WebSocket, escalation_id: str, role: str):
    """Handle WebSocket chat for escalation."""
    if role not in ["user", "admin"]:
        await websocket.close(code=4000)
        return

    escalation = get_escalation(escalation_id)
    if not escalation:
        await websocket.close(code=4001)
        return

    await websocket.accept()
    logger.info(f"WebSocket: {role} connected to {escalation_id}")

    # Register connection
    if escalation_id not in active_connections:
        active_connections[escalation_id] = {}
    active_connections[escalation_id][role] = websocket

    other_role = "admin" if role == "user" else "user"
    await _notify_party(escalation_id, other_role, f"{role.capitalize()} connected")

    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("message", "")

            # Forward message to other party (no storage)
            if other_role in active_connections.get(escalation_id, {}):
                try:
                    await active_connections[escalation_id][other_role].send_json({
                        "type": "message",
                        "role": role,
                        "message": message,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                except Exception:
                    pass

            # Echo back to sender for confirmation
            await websocket.send_json({
                "type": "message_sent",
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            })

    except WebSocketDisconnect:
        logger.info(f"WebSocket: {role} disconnected from {escalation_id}")
        if escalation_id in active_connections and role in active_connections[escalation_id]:
            del active_connections[escalation_id][role]
        await _notify_party(escalation_id, other_role, f"{role.capitalize()} disconnected")


async def _notify_party(escalation_id: str, role: str, message: str):
    """Send system notification to a party."""
    if role in active_connections.get(escalation_id, {}):
        try:
            await active_connections[escalation_id][role].send_json({
                "type": "system",
                "message": message
            })
        except Exception:
            pass


async def close_escalation_connections(escalation_id: str):
    """Close all WebSocket connections for an escalation."""
    if escalation_id in active_connections:
        for ws in active_connections[escalation_id].values():
            try:
                await ws.close()
            except Exception:
                pass
        del active_connections[escalation_id]
