@echo off
setlocal

set "ROOT_DIR=%~dp0"

set "TBLLM_DEVICE=auto"
set "TRANSFORMERS_NO_TF=1"
set "TF_ENABLE_ONEDNN_OPTS=0"
set "TOKENIZERS_PARALLELISM=false"
set "HF_HOME=%ROOT_DIR%.cache\huggingface"
set "TRANSFORMERS_CACHE=%HF_HOME%\transformers"
set "TBLLM_EMBEDDING_MODEL=%ROOT_DIR%models\embedding\paraphrase-multilingual-MiniLM-L12-v2"
set "TBLLM_EMBEDDING_LOCAL_ONLY=1"
set "TBLLM_BACKEND_PORT=5050"

if not exist "%TRANSFORMERS_CACHE%" mkdir "%TRANSFORMERS_CACHE%"

if not exist "%TBLLM_EMBEDDING_MODEL%\modules.json" (
    echo Warning: local embedding model not found at %TBLLM_EMBEDDING_MODEL%
    echo Run this once before vector retrieval: cd backEnd ^&^& python scripts\prepare_embedding_model.py
)

echo Starting TBLLM backend: http://127.0.0.1:5050
start "TBLLM Backend" /D "%ROOT_DIR%backEnd" cmd /k "where conda >nul 2>nul && conda run -n tbllm python app.py || (if exist .venv\Scripts\activate.bat call .venv\Scripts\activate.bat & if exist ..\.venv\Scripts\activate.bat call ..\.venv\Scripts\activate.bat & python app.py)"

echo Starting TBLLM frontend: http://localhost:5173
start "TBLLM Frontend" /D "%ROOT_DIR%frontEnd" cmd /k "npm run dev -- --host 127.0.0.1"

echo.
echo TBLLM is starting in two new terminal windows.
echo Close those windows to stop the services.

endlocal
