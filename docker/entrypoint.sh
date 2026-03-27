#!/bin/sh
set -e
# Fail fast with a clear import error (full traceback) before uvicorn hides it in async stack
echo "[entrypoint] Verifying application import..."
python -c "import main; print('[entrypoint] main import OK')"
exec uvicorn main:app --host 0.0.0.0 --port 8000 --loop asyncio --log-level info "$@"
