import os

mistral_embeddings = {
    "source": "rest",
    "apiKey": os.environ["MISTRAL_API_KEY"],
    "dimensions": 1024,
    "documentTemplate": "{{doc.document|truncatewords: 500}}",
    "url": "https://api.mistral.ai/v1/embeddings",
    "request": {"model": "mistral-embed", "input": ["{{text}}"]},
    "response": {"data": [{"embedding": "{{embedding}}"}]},
}

openai_embeddings = {
    "source": "openAi",
    "apiKey": os.getenv("OPENAI_API_KEY"),
    "model": os.getenv("OPENAI_EMBEDDING_MODEL"),
    "documentTemplate": "{{doc.document|truncatewords: 500}}",
}
