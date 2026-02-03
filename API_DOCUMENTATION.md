# Amrut Chatbot API Documentation

## Overview
This API provides an AI-powered chatbot with:
- **RAG Capability**: Queries Pinecone vector database for answers.
- **SQL Data**: Retrieves tourist information (coordinates) from Supabase.
- **Weather Enrichment**: Automatically fetches and appends live weather data for locations.
- **Admin Escalation**: Allows users to chat with valid admins via WebSocket when the AI cannot answer.

**Base URL**: `http://localhost:8000` (or your deployed URL)

---

## 1. Chatbot Endpoints

### 💬 Chat with the Bot
**Endpoint:** `POST /chatbot`  
**Description:** Main entry point for user queries. The AI processes the query through a workflow (Weather -> SQL -> Vector DB -> Evaluator).

**Request Body:**
```json
{
  "user_message": "tell me the tourist highlights in gondia?"
}
```

**Response (Success):**
```json
{
  "response": "The tourist highlights in Gondia are... \n\nCurrently, the weather is clear...",
  "escalation_required": false,
  "escalation_id": null,
  "websocket_url": null
}
```

**Response (Escalation Required):**
If the bot cannot answer (e.g. "I don't know"), it triggers escalation.
```json
{
    "response": "I don't know the answer to your question. Would you like to connect with an admin?",
    "escalation_required": true,
    "escalation_id": "550e8400-e29b-41d4-a716-446655440000",
    "websocket_url": "/ws/escalation/550e8400-e29b-41d4-a716-446655440000/user"
}
```

### 🗑️ Delete Document
**Endpoint:** `DELETE /chatbot/delete/{uuid}`  
**Description:** Deletes all vector embeddings associated with a source UUID.
**Path Parameters:**
- `uuid`: The source ID of the document to delete.

---

## 2. Admin Escalation Management

### 📋 List Pending Escalations
**Endpoint:** `GET /admin/escalations/pending`  
**Description:** Returns a list of all escalations waiting for an admin.
**Response:**
```json
{
  "status": "ok",
  "escalations": [
    {
      "escalation_id": "...",
      "user_question": "...",
      "status": "pending",
      "created_at": "2026-02-03T10:00:00"
    }
  ],
  "count": 1
}
```

### 📋 List Active Escalations
**Endpoint:** `GET /admin/escalations/active`  
**Description:** Returns escalations currently being handled by an admin.

### ✅ Accept Escalation
**Endpoint:** `PATCH /admin/escalations/{escalation_id}/accept`  
**Description:** Admin accepts a pending escalation to start chatting.
**Response:**
```json
{
  "status": "ok",
  "message": "Escalation accepted",
  "websocket_url": "/ws/escalation/{escalation_id}/admin"
}
```

### 🏁 Resolve Escalation
**Endpoint:** `PATCH /admin/escalations/{escalation_id}/resolve`  
**Description:** Marks the chat as resolved, closes WebSockets, and removes it from memory.
**Response:**
```json
{
  "status": "ok", 
  "message": "Escalation resolved and removed"
}
```

---

## 3. Real-Time Chat (WebSockets)

### 👤 User WebSocket
**URL:** `ws://{host}/ws/escalation/{escalation_id}/user`  
**Description:** Connects the user to the chat session. This URL is provided in the `/chatbot` response when `escalation_required` is true.

### 🛡️ Admin WebSocket
**URL:** `ws://{host}/ws/escalation/{escalation_id}/admin`  
**Description:** Connects the admin to the chat session. This URL is provided in the `/accept` endpoint response.

**Message Format (Both Sides):**
Send:
```json
{"message": "Hello, I need help"}
```

Receive:
```json
{
  "type": "message",
  "role": "user",  // or "admin"
  "message": "Hello, I need help",
  "timestamp": "..."
}
```

---

## 4. Document Upload

### 📤 Upload Document
**Endpoint:** `POST /upload/{uuid}`  
**Description:** Uploads and ingests a document (PDF, TXT, etc.) into the vector database.
**Content-Type:** `multipart/form-data`
**Parameters:**
- `uuid` (path): Unique ID for the document source.
- `file` (form-data): The file to upload.

**Response:**
```json
{
  "status": "ok",
  "message": "Document ingested successfully.",
  "source_id": "...",
  "namespace": "..."
}
```

---

## Environment Variables Required
The backend team needs to configure:
- `GOOGLE_API_KEY`: For Gemini LLM
- `OPENWEATHER_API_KEY`: For weather data
- `SUPABASE_URL` / `SUPABASE_KEY`: For SQL database (districts/coordinates)
- `PINECONE_API_KEY`: For vector database
- `NAMESPACE`: Pinecone namespace for documents
