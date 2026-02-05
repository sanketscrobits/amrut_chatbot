from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from src.Workflow.workflow import workflow
import re
from settings import NAMESPACE
from src.utils.vector_db.vector_store_factory import create_vector_store
from langchain_huggingface import HuggingFaceEmbeddings

# Initialize vector store using factory pattern
_embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vector_store = create_vector_store(embeddings=_embeddings)
from src.utils.escalation_manager import (create_escalation,get_escalation,handle_websocket_chat,close_escalation_connections)
# Import routers
from src.routers.admin_router import admin_router
from src.routers.upload_router import upload_router

app = FastAPI(title="Amrut Chatbot API", description="Chatbot with admin escalation support")


class ChatRequest(BaseModel):
    user_message: str

class ChatResponse(BaseModel):
    response: str
    escalation_required: bool = False
    escalation_id: Optional[str] = None
    websocket_url: Optional[str] = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["http://localhost:5173"] for stricter security
    allow_credentials=True,
    allow_methods=["*"],  # important for POST, GET, OPTIONS, etc.
    allow_headers=["*"],  # allow headers like Content-Type, Authorization
)

@app.get("/")
def root():
    return {"status": "ok", "message": "Chatbot API running"}

# Include routers
app.include_router(admin_router)
app.include_router(upload_router)

@app.post("/chatbot", response_model=ChatResponse)
async def chatbot_endpoint(request: ChatRequest):
    
    try:
        user_input = request.user_message
        print(f"User message: {user_input}")

        initial_state = {
            "user_query": user_input,
            "query_response": "",
            "evaluation_state": "",
            "retry_count": 0,
            "instruction": "",
            "data_source": "",
            "weather_info": "",
            "needs_escalation": False
        }

        final_state = workflow.invoke(initial_state, config={"verbose": True})
        print("Workflow final state:", final_state)

        query_response = final_state.get("query_response", "No response generated.")

        if "ValidationOutcome" in query_response:
           
            pattern = r'validated_output="((?:[^"\\]|\\.)*)"'
            match = re.search(pattern, query_response)
            if match:
                answer = match.group(1).replace('\\n', '\n').replace('\\"', '"').strip()
            else:
                
                fallback_pattern = r'validated_output=\'([^\']*)\'[, ]'
                fallback_match = re.search(fallback_pattern, query_response)
                if fallback_match:
                    answer = fallback_match.group(1).replace('\\n', '\n').replace('\\"', '"').replace("\\'", "'").strip()
                else:
                    
                    start_idx = query_response.find("validated_output='") + len("validated_output='")
                    end_idx = query_response.find("',\n    reask=", start_idx)
                    if end_idx != -1:
                        raw_content = query_response[start_idx:end_idx]
                        answer = raw_content.replace('\\n', '\n').replace('\\"', '"').replace("\\'", "'").strip()
                    else:
                        answer = "Error parsing validated output."
        else:
            
            answer = query_response.replace("'", "").strip().strip("'").strip()

        
        answer = re.sub(r'\n+$', '', answer).strip()

        # Check if escalation is needed (from workflow state)
        if final_state.get("needs_escalation", False):
            escalation = create_escalation(
                user_question=user_input,
                context=answer
            )
            return ChatResponse(
                response=answer,
                escalation_required=True,
                escalation_id=escalation["escalation_id"],
                websocket_url=f"/ws/escalation/{escalation['escalation_id']}/user"
            )
        
        return ChatResponse(response=answer)

    except Exception as e:
        print("Error in /chatbot:", e)
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/chatbot/delete/{uuid}")
async def delete_document(uuid: str):
    """Delete all chunks associated with the provied UUID source."""
    try:
        if not NAMESPACE:
             raise HTTPException(status_code=500, detail="NAMESPACE configuration missing.")
        
        if not vector_store:
            raise HTTPException(status_code=500, detail="Vector Store not initialized.")

        vector_store.delete_by_source(source=uuid, namespace=NAMESPACE)
        
        return {"status": "ok", "message": f"Deleted documents with source {uuid} from namespace {NAMESPACE}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# User WebSocket Endpoint for Escalation Chat
@app.websocket("/ws/escalation/{escalation_id}/user")
async def websocket_user_chat(websocket: WebSocket, escalation_id: str):
    """
    WebSocket for user real-time chat with admin during escalation.
    """
    escalation = get_escalation(escalation_id)
    if not escalation:
        await websocket.close(code=4001)
        return
    
    await handle_websocket_chat(websocket, escalation_id, "user")


# python -m uvicorn src.main.chatbotapi:app --reload