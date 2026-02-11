from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from typing import Optional
import re
import json
import asyncio
import time
from contextlib import asynccontextmanager
from sse_starlette.sse import EventSourceResponse

from src.Workflow.master_workflow import workflow
from src.settings import NAMESPACE
from src.utils.vector_db.vector_store_factory import create_vector_store
from langchain_huggingface import HuggingFaceEmbeddings
from src.utils.db_connection import get_supabase_db
from src.utils.response_cache import get_cached_response, cache_response
from src.utils.semantic_cache import get_semantic_cached_response, cache_semantic_response
from src.utils.escalation_manager import (
    create_escalation, 
    get_escalation, 
    handle_websocket_chat, 
    close_escalation_connections
)
from src.routers.admin_router import admin_router
from src.routers.upload_router import upload_router
from src.utils.llm_singleton import get_streaming_llm

# Initialize vector store using factory pattern
vector_store = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global vector_store
    
    # Initialize Vector Store (Lazy Load to prevent import blocking)
    try:
        print("[STARTUP] 🧠 Initializing Vector Store...")
        _embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        vector_store = create_vector_store(embeddings=_embeddings)
        print("[STARTUP] ✅ Vector Store initialized.")
    except Exception as e:
        print(f"[STARTUP] ⚠️ Vector Store init failed: {e}")

    # Eagerly initialize DB connection pool to avoid cold start latency on first request
    # OPTIMIZATION: Pre-warm pool on startup for instant first query
    try:
        print("[STARTUP] 🔥 Pre-warming database connection pool (Background Task)...")
        
        async def warm_up_db():
            try:
                t0 = time.time()
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, get_supabase_db)
                t1 = time.time()
                print(f"[STARTUP] ✅ Database pool ready in {t1-t0:.2f}s")
            except Exception as e:
                print(f"[STARTUP] ⚠️  Failed to pre-warm DB pool: {e}")

        # Fire and forget (don't await)
        asyncio.create_task(warm_up_db())
        
    except Exception as e:
        print(f"[STARTUP] ⚠️  Failed to start DB pre-warm task: {e}")
    yield
    # Cleanup if needed

app = FastAPI(title="Amrut Chatbot API", description="Chatbot with admin escalation support", lifespan=lifespan)

# Query validation constants
MAX_QUERY_LENGTH = 5000
MIN_QUERY_LENGTH = 1


class ChatRequest(BaseModel):
    user_message: str
    
    @field_validator('user_message')
    @classmethod
    def validate_message(cls, v):
        if not v or not v.strip():
            raise ValueError("Query cannot be empty. Please provide a valid question.")
        if len(v) > MAX_QUERY_LENGTH:
            raise ValueError(f"Query too long ({len(v)} chars). Maximum length: {MAX_QUERY_LENGTH} characters.")
        return v

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
        
        # Validate query is not empty
        if not user_input or not user_input.strip():
            raise HTTPException(
                status_code=400,
                detail="Query cannot be empty. Please provide a valid question."
            )
        
        # Validate query length
        if len(user_input) > MAX_QUERY_LENGTH:
            raise HTTPException(
                status_code=400,
                detail=f"Query too long ({len(user_input)} chars). Maximum length: {MAX_QUERY_LENGTH} characters."
            )
        
        print(f"User message: {user_input}")
        
        # PHASE 7: Semantic caching - find semantically similar queries
        cached_response = get_semantic_cached_response(user_input)
        if cached_response:
            return ChatResponse(**cached_response)
        
        # Fallback to exact match cache
        cached_response = get_cached_response(user_input)
        if cached_response:
            return ChatResponse(**cached_response)

        initial_state = {
            "validated_user_input": user_input,
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
        needs_escalation = final_state.get("needs_escalation", False)
        escalation_id = None
        websocket_url = None

        if needs_escalation:
            escalation = create_escalation(
                user_question=user_input,
                context=answer
            )
            escalation_id = escalation["escalation_id"]
            websocket_url = f"/ws/escalation/{escalation_id}/user"
        
        response_data = {
            "response": answer,
            "escalation_required": needs_escalation,
            "escalation_id": escalation_id,
            "websocket_url": websocket_url
        }
        
        # PHASE 7: Cache with semantic indexing
        cache_semantic_response(user_input, response_data, ttl=900)
        
        # Also cache with exact match (backward compatibility)
        cache_response(user_input, response_data)
        
        return ChatResponse(**response_data)

    except HTTPException:
        raise
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



# --------------------------------------------------------------------------
# Phase 7: Streaming Responses (SSE)
# --------------------------------------------------------------------------

@app.post("/chatbot/stream")
async def chatbot_stream_endpoint(request: ChatRequest):
    """
    Streaming endpoint for Chatbot.
    Returns Server-Sent Events (SSE) with token-by-token response.
    """
    async def event_generator():
        try:
            user_input = request.user_message
            
            # Helper to format SSE message
            def format_sse(data):
                return {"event": "message", "data": json.dumps(data)}
            
            # 1. Check Cache First (Instant Response)
            # ---------------------------------------
            # Try semantic cache first
            cached_response = get_semantic_cached_response(user_input)
            if not cached_response:
                # Try exact match cache
                cached_response = get_cached_response(user_input)
                
            if cached_response:
                # If cached, stream it as a single chunk (effectively instant)
                response_text = cached_response.get("response", "")
                yield format_sse({"token": response_text, "done": True, "cached": True})
                return

            # 2. Run Workflow (Streaming Mode)
            # --------------------------------
            # NOTE: Full LangGraph streaming requires structural changes.
            # For Phase 7, we simulate streaming by running the workflow and 
            # then streaming the final synthesis step if possible, or 
            # just yielding the final result.
            
            # Ideally, we would use .astream_events() on the graph, but 
            # our graph structure needs to support it. 
            # For now, we will execute the workflow and yield the result.
            # This is a "Pseudo-Stream" for now to establish the contract.
            
            initial_state = {
                "validated_user_input": user_input,
                "query_response": "",
                "evaluation_state": "",
                "retry_count": 0,
                "instruction": "",
                "data_source": "",
                "weather_info": "",
                "needs_escalation": False
            }
            
            # Run workflow (awaiting full execution)
            Loop = asyncio.get_event_loop()
            final_state = await Loop.run_in_executor(None, workflow.invoke, initial_state)
            
            query_response = final_state.get("query_response", "No response generated.")
            
            # Parse response (reuse logic from main endpoint)
            answer = query_response
            if "ValidationOutcome" in str(query_response):
                # ... extraction logic ...
                # Simplified for stream (robust logic is in main endpoint)
                 match = re.search(r'validated_output="((?:[^"\\]|\\.)*)"', str(query_response))
                 if match:
                     answer = match.group(1).replace('\\n', '\n').replace('\\"', '"').strip()
                 else:
                     start_idx = str(query_response).find("validated_output='") + len("validated_output='")
                     if start_idx > len("validated_output='"):
                         answer = str(query_response)[start_idx:].split("',")[0].strip()
            
            answer = str(answer).replace("'", "").strip().strip("'").strip()
            
            # Stream the result token by token (Simulated for UX)
            # In a real full-async refactor, we would stream directly from the LLM
            tokens = answer.split(" ")
            for token in tokens:
                yield format_sse({"token": token + " ", "done": False})
                await asyncio.sleep(0.01) # Small delay to simulate typing
            
            # Cache the result
            response_data = {
                "response": answer,
                "escalation_required": final_state.get("needs_escalation", False)
            }
            cache_semantic_response(user_input, response_data, ttl=900)
            cache_response(user_input, response_data)

            yield format_sse({"done": True})

        except Exception as e:
            yield format_sse({"error": str(e), "done": True})

    return EventSourceResponse(event_generator())


# python -m uvicorn src.main.chatbotapi:app --reload