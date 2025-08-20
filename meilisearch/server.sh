#!/bin/bash
source .env

## Check for the presence of meilisearch file
if [ ! -f ./meilisearch_binary ]; then
    echo "Downloading Meilisearch..."
    curl -L https://install.meilisearch.com | sh
    mv meilisearch meilisearch_binary
    echo "Download complete."
fi

## Start the server locally
./meilisearch_binary