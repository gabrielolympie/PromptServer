## UPDATE IN PROGRESS (ETA 12/07/2025):
- recursive tool use intégration
- openapi documentation
- rate limiting
- temporally signed bearer token security
- logfire seamless integration
- tags in logging system for observability

# Prompt Server

A FastAPI server that simply serve prompts, no code required.

## Why Prompt Server?

- Eliminates repetitive boilerplate code for prompt handling
- Enables rapid iteration by modifying prompts without code changes
- Standardizes prompt management across projects
- Simplifies integration with frontend applications

## Features

- **Prompt-first architecture**: Define prompts as markdown files - no additional code needed
- **Multi-provider support**: Works with any provider supported by [LiteLLM](https://docs.litellm.ai/docs/providers)
- **Multimodal capabilities**: Handle text, images, audio, video, and documents (varies by provider)
- **Streaming responses**: Get interleaved text and structured outputs
- **Automatic routing**: Prompt file paths become API endpoints automatically
- **Retry & fallback**: Built-in retry logic and fallback model support
- **Docker-ready**: Easy containerization for deployment

## Supported Modalities (April 2025)

| Type       | Anthropic | Cohere | Gemini | Groq | Mistral | OpenAI |
|------------|-----------|--------|--------|------|---------|--------|
| Text       | ✓         | ✓      | ✓      | ✓    | ✓       | ✓      |
| Image      | ✓         | -      | ✓      | ✓    | ✓       | ✓      |
| Audio      | -         | -      | ✓      | -    | -       | ✓      |
| Video      | -         | -      | ✓      | -    | -       | -      |
| Document   | ✓         | -      | -      | -    | -       | -      |

## Getting Started

### Prerequisites
- Python 3.8+
- API keys for your desired LLM providers

### Local Installation

1. **Configure environment**:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` with your API keys and settings.

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the server**:
   ```bash
   python app.py
   ```

4. **See doc**:
    Navigate to http://localhost:8080/docs (port might changed based on your env) to see your routes.

### Docker Installation
```bash
docker build -t prompt-server .
docker run -p 8080:8080 --env-file .env prompt-server
```

## Defining Prompts

Create markdown files in the `prompts/` directory (configurable via `PROMPT_PATH` in `.env`).

### Prompt File Structure
````markdown
```yaml
# Configuration (YAML frontmatter)
call:
  model: gemini-1.5-flash-8b
  stream: true
  json_mode: false
  tools: []
  call_params:
    temperature: 0.3
    top_p: 0.95
retry: 3
fallback: os.environ['FALLBACK_MODEL']
parse_objects: true
```

## PROMPTFILE

SYSTEM:
You are a helpful assistant

---

MESSAGES:

{history}

---

ASSISTANT:

OK

---

USER:

##### TASK

Describe the following image:
{image:image}

##### OUTPUT

First write a free form description, then provide structured YAML:

###### DESCRIPTION
[Your description here]

###### YAML DESCRIPTION
```yaml
subject: [main subject]
context: [image context]
```
````

The file path determines the API endpoint. For example:
- `prompts/chat.md` → `/prompt_server/chat`
- `prompts/nested/describe.md` → `/prompt_server/nested/describe`

## Roadmap

- OpenAPI documentation generation from prompts
- Expanded streaming support for audio/video outputs
- Client libraries (React & Python)
- Enhanced authentication mechanisms



## License

[MIT](LICENSE) (Note: You may want to add a proper license file)# prompt-server
