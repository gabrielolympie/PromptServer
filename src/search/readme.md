# Search
Search will be based on meilisearch engine, you will find in this folder utilities to tune and configure the search database.

Warning, this only for settings, regarding querying the search database, look in the clients folder.

## Embeddings
Embeddings are used to convert text into a vector representation. This is useful for semantic search.

You'll find several scripts to run AFTER launching the meilisearch server.
If your meilisearch url contains localhost, the server will be launched automatically when running the server.sh script of the backend
- enable.sh : Enable the embedding feature of meilisearch
- disable.sh : Disable the embedding feature of meilisearch
- openai.sh : Configure meilisearch to use openai embedding, based on env variables (you can also trick it to use another provider with open ai compatible api)
- mistral.sh : Configure meilisearch to use mistral embedding, based on env variables, this one also serve as an example on how to query any http based embedding provider

When running from the local server, the embedding dump will be stored directly in the container. Hence it is recommended to avoid using vectors as this will quickly increase the database size.