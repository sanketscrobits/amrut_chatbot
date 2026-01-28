# Query-Agent

## Overview

Query-Agent is an AI-powered question-answering system that retrieves context from indexed documents (such as PDFs) and answers user queries using advanced language models and vector search. It is built with FastAPI, LangChain, Pinecone, and integrates with WhatsApp for conversational interfaces.

---

## Project Structure

```
Query-Agent/
│
├── chatbot_ui/
├── documents/
├── src/
│   ├── agents/
│   │   ├── evaluator_agent.py
│   │   ├── query_agent.py
│   │   └── retriver_agent.py
│   ├── document_loader/
│   │   ├── local_loader.py
│   │   ├── prompt.txt
│   │   ├── prompt2.txt
│   │   └── web_scraper.py
│   ├── main/
│   │   ├── chatbotapi.py
│   │   └── main.py
│   ├── schemas/
│   │   ├── evaluation_schema.py
│   │   └── response_schema.py
│   ├── tools/
│   │   └── query_tool.py
│   ├── Uploader/
│   │   ├── upload_api.py
│   │   └── uploader_pinecone.py
│   ├── utils/
│   │   ├── vector_db/
│   │   ├── mermaid_graph_generator.py
│   │   ├── prompts.yml
│   │   └── yaml_loader.py
│   └── Workflow/
│       └── workflow.py
├── .dockerignore
├── .env
├── .gitignore
├── .python-version
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── README.md
├── settings.py
└── uv.lock
```

---

## Functional Description

### 1. Document Loading

- **local_loader.py**: Loads and extracts text from PDF documents using `pypdf`. The extracted text is cleaned and made available for further processing or indexing.

### 2. Context Retrieval

- **query_tool.py**: Provides the `get_context` tool, which uses a sentence transformer to embed user questions and queries Pinecone for the most relevant document chunk. Returns the most relevant context or a message if no context is found.

### 3. Agent Logic

- **qurey_agent.py**: Defines the main agent using LangChain's agent framework. Uses Google Gemini LLM via `langchain_google_genai`. The agent is configured to always use the `get_context` tool to answer questions. The agent is exportable and can be invoked from other modules.

### 4. API Layer

- **main.py**: Implements a FastAPI server with endpoints for health checks and WhatsApp webhook integration. Receives WhatsApp messages, extracts the user's question, and invokes the agent. Returns the agent's answer as a WhatsApp message.
- **supervisor.py**: (Not fully shown) Likely coordinates agent execution and may handle advanced workflows or multi-agent orchestration.

### 5. Configuration

- **settings.py**: Loads environment variables for API keys, Pinecone configuration, and WhatsApp integration.
- **pyproject.toml**: Lists all dependencies, including FastAPI, LangChain, Pinecone, Google GenAI, pypdf, and more.

---

## Technical Details

### Key Technologies

- **FastAPI**: REST API framework for serving the agent and handling webhooks.
- **LangChain**: Framework for building LLM-powered agents and tools.
- **Pinecone**: Vector database for semantic search and context retrieval.
- **Google Gemini (via LangChain)**: Large Language Model for answering questions.
- **pypdf**: PDF parsing and text extraction.
- **dotenv**: Loads environment variables from `.env` files.

### Data Flow

1. **Document Ingestion**: PDF files are loaded and text is extracted (`local_loader.py`). Text is (presumably) indexed in Pinecone for semantic search.
2. **User Query**: User sends a question (e.g., via WhatsApp). FastAPI receives the webhook, extracts the question, and passes it to the agent.
3. **Context Retrieval**: The agent uses the `get_context` tool to embed the question and search Pinecone for relevant context.
4. **Answer Generation**: The agent uses the retrieved context and the LLM to generate a response. The answer is sent back to the user (e.g., via WhatsApp).

### Error Handling

- If no relevant context is found, the agent returns a default message.
- If an error occurs during context retrieval, it is caught and returned as an error message.

---

## Extensibility

- **Adding New Tools**: Additional tools can be created and registered with the agent for more advanced workflows.
- **Multi-Agent Support**: The presence of a `supervisor.py` suggests support for multi-agent orchestration.
- **API Integrations**: Easily extendable to other messaging platforms or frontends by adding new endpoints.

---

## Security & Deployment

- **API Keys**: All sensitive keys are loaded from environment variables.
- **Production Readiness**: Use environment variables for all secrets and tokens. Consider deploying with a production ASGI server (e.g., Uvicorn or Gunicorn).

---

## Usage

### Run the API server

```sh
uv pip run python -m src.main.main
```

### Interact with the agent

- Send a WhatsApp message to the configured number.
- Or, invoke the agent directly in Python:
  ```python
  from src.agents.qurey_agent import query_agent
  result = query_agent.invoke({"input": "Your question here"})
  print(result["output"])
  ```

---

## Recommendations

- Add more robust error handling and logging for production use.
- Ensure all documents to be queried are indexed in Pinecone.
- Add unit and integration tests for all modules.
