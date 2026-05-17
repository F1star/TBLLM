# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Project Overview

This is a "青少年综合能力评价系统" (Comprehensive Ability Evaluation System for Adolescents) – a graduation project that uses large language models to evaluate students' abilities based on text submissions and interactive dialogues. The system analyzes materials (essays, summaries) and chat content to generate multi‑dimensional ability scores and textual feedback.

The system follows a three‑layer architecture:
- **Frontend**: Vue 3 + Vite single‑page application for material upload, chat interface, and result visualization.
- **Backend**: Flask REST API that handles authentication, file parsing, LLM inference, and evaluation.
- **Model layer**: Locally deployed causal language model (Qwen1.5‑1.8B‑Chat) called via Transformers, with a custom agent service that formats prompts and manages conversation history.

## Development Setup

### Backend (Flask)
- Python dependencies are listed in `backEnd/requirements.txt`.  
  **Important**: The `torch` packages are pinned to CUDA‑enabled versions; if you only have CPU, you may need to adjust the `--extra-index‑url` line or install CPU‑only wheels.
- Install dependencies:
  ```bash
  cd backEnd
  pip install -r requirements.txt
  ```
- Environment variables: no `.env` is required; environment flags are set in `backEnd/utils/environment.py`.
- The database is SQLite (`instance/users.db`). Tables are created automatically when `app.py` starts (`db.create_all()`).
- Run the development server:
  ```bash
  python app.py
  ```
  The server will listen on `http://127.0.0.1:5000` with CORS configured for `http://localhost:5173` (the default Vite dev server).

### Frontend (Vue 3 + Vite)
- Node.js dependencies are in `frontEnd/package.json`.
- Install and run:
  ```bash
  cd frontEnd
  npm install
  npm run dev
  ```
- The dev server starts on `http://localhost:5173`.
- The frontend expects the backend API at `http://127.0.0.1:5000/api`. This is configured in the Vue components (check `src/components/` for `fetch` URLs).

### Model Files
- The default model is `Qwen1.5‑1.8B‑Chat`, stored under `models/Qwen1.5‑1.8B‑Chat/`.
- The path is defined in `backEnd/config/constants.py` (`MODEL_PATH`). If you want to use a different model, update that constant and ensure the new model directory follows the Hugging Face Transformers layout.
- The model is loaded lazily when the first request arrives; watch the console for “Loading local model from: …”.

## Key Architecture Points

### Backend Structure
- `backEnd/app.py` – Flask application entry point. Registers routes, creates database tables, and adds a pre‑request check that blocks concurrent model inference.
- `backEnd/config/` – Flask app configuration, constants (model path, prompt templates), and JWT setup.
- `backEnd/routes/` – REST endpoint handlers (auth, chat, evaluation, file upload).
- `backEnd/services/` – Business logic:
  - `model_service.py`: Singleton that loads the Transformers model and tokenizer; provides `generate_response()` and `generate_evaluation()`.
  - `agent_service.py`: Wraps the LLM with custom prompts for chat and evaluation.
  - `chat_service.py`, `evaluation_service.py`, `file_service.py`: Domain‑specific operations.
- `backEnd/db_models/` – SQLAlchemy models for User, File, ChatHistory, Evaluation.
- `backEnd/uploads/` – Directory where uploaded documents are stored.

### Frontend Structure
- `frontEnd/src/App.vue` – Root component with router‑view.
- `frontEnd/src/components/` – Vue components for login, chat, file upload, evaluation dashboard.
- `frontEnd/src/assets/` – Static images.
- `frontEnd/public/` – Public assets.
- The frontend uses the native `fetch` API for HTTP calls and Chart.js for visualization of evaluation scores.

### API Endpoints
All endpoints are prefixed with `/api/`:

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST   | `/api/register` | Create a new user |
| POST   | `/api/login` | Authenticate and receive a JWT |
| POST   | `/api/change‑password` | Change password (requires JWT) |
| POST   | `/api/chat` | Send a message to the LLM, returns streaming response |
| POST   | `/api/chat/clear` | Clear chat history for the current user |
| GET    | `/api/chat/history` | Retrieve recent chat history |
| POST   | `/api/evaluate` | Trigger an overall evaluation based on chat history and uploaded files |
| GET    | `/api/evaluation/latest` | Fetch the latest evaluation result |
| GET    | `/api/evaluations` | List all evaluations for the user |
| POST   | `/api/files/upload` | Upload a document (PDF, Word) |
| GET    | `/api/files` | List user’s uploaded files |
| GET    | `/api/files/<id>` | Get metadata and extracted text of a file |
| GET    | `/api/files/<id>/download` | Download the original file |
| DELETE | `/api/files/<id>` | Delete a file |

Authentication uses JSON Web Tokens (Flask‑JWT‑Extended). Most endpoints require the `Authorization: Bearer <token>` header.

### Model Inference & Prompting
- The `ModelService` uses a thread lock to prevent concurrent generation (the GPU memory cannot handle multiple inferences at once).
- Chat prompts are built by `agent_service.py` using a history of the last 10 messages (formatted as “role: content”).
- Evaluation prompts are defined in `backEnd/config/constants.py` (`EVALUATION_PROMPT_TEMPLATE`). The agent service injects chat history and file context, then parses the LLM’s JSON response.
- The model runs in eval mode with cache enabled. If a “CUDA out of memory” error occurs, the cache is cleared and a user‑friendly message is returned.

### Database Schema
- `User`: id, username, password (hashed), created_at
- `File`: id, user_id, filename, original_filename, file_path, upload_time, extracted_text
- `ChatHistory`: id, user_id, role (‘user’ or ‘assistant’), content, timestamp
- `Evaluation`: id, user_id, logic_score, creativity_score, expression_score, knowledge_score, overall_score, feedback, created_at

## Common Development Tasks

### Running a Single Component
- **Backend**: Start the Flask dev server as above. The server will reload on file changes (debug mode is on).
- **Frontend**: Run `npm run dev` in the frontEnd directory. Use `npm run build` for a production bundle, `npm run preview` to serve the built assets locally.

### Testing the API
You can use curl or a REST client. Example login and chat:
```bash
# Login
curl -X POST http://127.0.0.1:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}'

# Use the returned token in subsequent requests
curl -X POST http://127.0.0.1:5000/api/chat \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello, how are you?"}'
```

### Adding a New API Endpoint
1. Create a new function in the appropriate `routes/*_routes.py` file.
2. Import and register it in `routes/__init__.py` (`register_routes`).
3. If needed, add a corresponding service method in `services/`.
4. The endpoint will automatically be protected by JWT if it follows the existing pattern.

### Modifying the Evaluation Criteria
Edit the `EVALUATION_PROMPT_TEMPLATE` in `backEnd/config/constants.py`. The template is filled with `{chat_content}` and expects a JSON response with the fields `logic_score`, `creativity_score`, `expression_score`, `knowledge_score`, `overall_score`, and `feedback`.

### Switching the Language Model
1. Place the new model files under `models/` (or anywhere else).
2. Update `MODEL_PATH` in `backEnd/config/constants.py` to point to the new directory.
3. Ensure the model is compatible with Hugging Face `AutoModelForCausalLM` and `AutoTokenizer`.
4. Restart the Flask server; the model will be reloaded on the first request.

## LangChain Framework Integration

The system now includes enhanced LangChain components for better agent capabilities and semantic document retrieval.

### Advanced Agent System
- **AdvancedAgent**: A complete LangChain AgentExecutor implementation using ReAct pattern, supporting tool calling and reasoning.
- **Tool System**: Multiple built-in tools including time, calculator, document retrieval, evaluation calling, and session management.
- **Configuration**: Switch between original AgentService and AdvancedAgent via `USE_ADVANCED_AGENT` in `backEnd/config/constants.py`.

### Vector Store & Enhanced RAG
- **Vector Storage**: ChromaDB-based vector store with user-isolated collections.
- **Embedding Model**: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` for Chinese text embeddings.
- **Hybrid Retrieval**: Combines vector semantic search with keyword matching as fallback.
- **Automatic Indexing**: Uploaded documents are automatically indexed into vector storage via `RAGService.add_documents_to_vector_store()`.

### Key Files
- `backEnd/services/advanced_agent.py` - AdvancedAgent implementation
- `backEnd/services/agent_tools_enhanced.py` - Enhanced tool system
- `backEnd/services/vector_store.py` - ChromaDB vector store service
- `backEnd/services/rag_service.py` - Enhanced RAG with vector retrieval
- `backEnd/config/constants.py` - Configuration flags (`USE_ADVANCED_AGENT`, `USE_VECTOR_RETRIEVAL`, etc.)

### Usage
1. **Enable AdvancedAgent**: Set `USE_ADVANCED_AGENT = True` in `constants.py`.
2. **Enable Vector Retrieval**: Set `USE_VECTOR_RETRIEVAL = True` (default).
3. **Upload Documents**: Files are automatically indexed; vector storage persists at `backEnd/vector_store/`.
4. **Agent Tools**: The AdvancedAgent can use tools like `get_current_time`, `calculator`, etc.

### Dependencies
Added dependencies in `backEnd/requirements.txt`:
- `chromadb==0.5.23`
- `sentence-transformers==3.3.1`
- `langchain-experimental==0.0.69`
- `pytest==8.3.4` (for testing)

## Notes & Pitfalls

- **Concurrent requests**: The model service uses a global lock (`generate_lock`). If two users try to generate at the same time, the second will receive a 429 “模型正在生成，请稍后再试” response. This is intentional to avoid OOM errors.
- **File uploads**: Uploaded documents are saved to `backEnd/uploads/` with a timestamped name. Extracted text is stored in the database; the original file is kept for download.
- **Token limits**: The context length is limited to `MAX_CONTEXT_CHARS` (800 characters) per chat turn and `MAX_NEW_TOKENS` (128) for generation. Adjust these constants if longer responses are needed.
- **GPU memory**: The model loads in FP16 on CUDA if available, otherwise FP32 on CPU. If you encounter CUDA OOM, reduce `MAX_NEW_TOKENS` or switch to a smaller model.
- **Secret keys**: The JWT and file‑encryption secret keys are hard‑coded in `config/settings.py`. **Change them before deploying to production.**

## Where to Look For…

- **Frontend API calls**: Check `frontEnd/src/components/` for Axios instances and request URLs.
- **Database models**: `backEnd/db_models/`.
- **Prompt engineering**: `backEnd/config/constants.py` and `backEnd/services/agent_service.py`.
- **Authentication logic**: `backEnd/routes/auth_routes.py` and `backEnd/config/settings.py` (JWT setup).
- **File parsing**: `backEnd/services/file_service.py` (uses PyPDF2 and python‑docx).
