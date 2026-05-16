#!/bin/sh
set -e

echo "Waiting for ChromaDB..."
until curl -sf http://chromadb:8000/api/v2/heartbeat > /dev/null; do
  sleep 2
done
echo "ChromaDB is ready."

echo "Seeding ChromaDB..."
python seed_chroma.py

echo "Starting API server..."
exec uvicorn src.api.server:app --host 0.0.0.0 --port 8080