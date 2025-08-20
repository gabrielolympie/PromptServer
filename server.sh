#!/bin/bash

# source .env

# Launch redis server
# redis-server --port 3501 &

# Check if LAUNCH_MEILISEARCH is true, then launch Meilisearch non-blockingly
# if [ "$LAUNCH_MEILISEARCH" = "true" ]; then
#   (
#     cd ./meilisearch
#     ./server.sh
#   ) &
# fi

# Start uvicorn (main app)
uvicorn app:app --host 127.0.0.1 --port 8080 --reload --workers 20