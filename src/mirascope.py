from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from mirascope import llm, prompt_template
from mirascope.retries import FallbackError, fallback
from tenacity import RetryError, retry, stop_after_attempt, wait_exponential
from typing import Iterator, List, Dict, Any, Optional, Union, AsyncIterator
from dotenv import load_dotenv
import logfire
import yaml
import json
import os
import re

load_dotenv()

if "LOGFIRE_TOKEN" in os.environ:
    logfire.configure()

class ContentParser:
    """Base class for content parsers"""
    def __init__(self, pattern: str):
        self.pattern = re.compile(pattern, re.DOTALL)
        self.processed_blocks = set()
    
    def find_blocks(self, text: str) -> List[str]:
        return [match.strip() for match in self.pattern.findall(text)]
    
    def parse(self, content: str) -> Any:
        raise NotImplementedError
    
    def process(self, text: str) -> Iterator[Dict[str, Any]]:
        for block in self.find_blocks(text):
            if block not in self.processed_blocks:
                self.processed_blocks.add(block)
                try:
                    parsed = self.parse(block)
                    yield {"content": parsed, "format":'object'}
                except Exception as e:
                    yield {"error": str(e), "block": block, "format": self.__class__.__name__.lower()}

class YamlParser(ContentParser):
    def __init__(self):
        super().__init__(r'```yaml(.*?)```')
    
    def parse(self, content: str) -> Any:
        return yaml.safe_load(content)

class JsonParser(ContentParser):
    def __init__(self):
        super().__init__(r'```json(.*?)```')
    
    def parse(self, content: str) -> Any:
        return json.loads(content)

class StreamProcessor:
    def __init__(self):
        self.parsers = [YamlParser(), JsonParser()]
        self.full_response = ""
    
    def process_stream(self, stream: Iterator, parse_objects=True) -> Iterator[str]:
        """Process a stream of chunks and yield parsed content as JSON strings"""
        for chunk, _ in stream:
            self.full_response += chunk.content
            
            if parse_objects:
                yield from self._process_content()
                
            yield json.dumps({'content':chunk.content, 'format':'text'})
    
    def _process_content(self) -> Iterator[str]:
        """Process the accumulated content through all parsers"""
        for parser in self.parsers:
            for result in parser.process(self.full_response):
                yield json.dumps(result)

def dummy_decorator(func):
    return func

def load_prompt(prompt_path):
    with open(prompt_path, 'r') as f:
        prompt=f.read()
    
    config, template = prompt.split("## PROMPTFILE")
    pattern = re.compile(r'```yaml(.*?)```', re.DOTALL)
    
    config = pattern.findall(config)[0]
    config = yaml.safe_load(config)
    
    if "os.environ" in config['call']['model']:
        config['call']['model'] = eval(config['call']['model'])
    
    template = template.replace("\n\n---\n\n","\n").strip()
    return config, template

def create_mirascope_call(prompt_path):
    config, template=load_prompt(prompt_path)

    retry_decorator=dummy_decorator
    fallback_decorator=dummy_decorator
    if 'retry' in config:
        retry_decorator = retry(stop=stop_after_attempt(config['retry']),wait=wait_exponential(multiplier=1, min=4, max=10))

        if 'fallback' in config: ## fallback is enabled only if retry is as well
            fallback_decorator = fallback(RetryError,[{"catch": RetryError,"provider": "litellm","model": config['fallback'],}])

    @fallback_decorator
    @retry_decorator
    @llm.call('litellm', **config['call'])
    @prompt_template(template)
    def call_mirascope(**kwargs): ...

    return config, call_mirascope

def stream_output_logfire(stream: Iterator, logfire_metadata: dict = None, parse_objects=True) -> Iterator[str]:
    """Public interface for streaming output processing"""
    processor = StreamProcessor()
    yield from processor.process_stream(stream, parse_objects=parse_objects)

    if "LOGFIRE_TOKEN" in os.environ:
        if logfire_metadata is not None:
            logfire.info(
                processor.full_response,
                attributes=logfire_metadata,
            )

class AsyncContentParser:
    """Base class for async content parsers"""
    def __init__(self, pattern: str):
        self.pattern = re.compile(pattern, re.DOTALL)
        self.processed_blocks = set()
    
    def find_blocks(self, text: str) -> List[str]:
        return [match.strip() for match in self.pattern.findall(text)]
    
    async def parse(self, content: str) -> Any:
        raise NotImplementedError
    
    async def process(self, text: str) -> AsyncIterator[Dict[str, Any]]:
        for block in self.find_blocks(text):
            if block not in self.processed_blocks:
                self.processed_blocks.add(block)
                try:
                    parsed = await self.parse(block)
                    yield {"content": parsed, "format": 'object'}
                except Exception as e:
                    yield {"error": str(e), "block": block, "format": self.__class__.__name__.lower()}

class AsyncYamlParser(AsyncContentParser):
    def __init__(self):
        super().__init__(r'```yaml(.*?)```')
    
    async def parse(self, content: str) -> Any:
        return yaml.safe_load(content)

class AsyncJsonParser(AsyncContentParser):
    def __init__(self):
        super().__init__(r'```json(.*?)```')
    
    async def parse(self, content: str) -> Any:
        return json.loads(content)

class AsyncStreamProcessor:
    def __init__(self):
        self.parsers = [AsyncYamlParser(), AsyncJsonParser()]
        self.full_response = ""
    
    async def process_stream(self, stream: AsyncIterator, parse_objects=True) -> AsyncIterator[str]:
        """Process a stream of chunks asynchronously and yield parsed content as JSON strings"""
        async for chunk, _ in stream:
            self.full_response += chunk.content
            if parse_objects:
                async for result in self._process_content():
                    yield result
            yield json.dumps({'content': chunk.content, 'format': 'text'})
    
    async def _process_content(self) -> AsyncIterator[str]:
        """Process the accumulated content through all parsers asynchronously"""
        for parser in self.parsers:
            async for result in parser.process(self.full_response):
                yield json.dumps(result)

async def async_load_prompt(prompt_path):
    with open(prompt_path, 'r') as f:
        prompt = f.read()
    config, template = prompt.split("## PROMPTFILE")
    pattern = re.compile(r'```yaml(.*?)```', re.DOTALL)
    config = pattern.findall(config)[0]
    config = yaml.safe_load(config)
    if "os.environ" in config['call']['model']:
        config['call']['model'] = eval(config['call']['model'])
    template = template.replace("\n\n---\n\n", "\n").strip()
    return config, template

async def async_create_mirascope_call(prompt_path):
    config, template = await async_load_prompt(prompt_path)
    retry_decorator = dummy_decorator
    fallback_decorator = dummy_decorator
    
    if 'retry' in config:
        retry_decorator = retry(stop=stop_after_attempt(config['retry']), wait=wait_exponential(multiplier=1, min=4, max=10))
    
    if 'fallback' in config:
        fallback_decorator = fallback(RetryError, [{"catch": RetryError, "provider": "litellm", "model": config['fallback']}])
    
    @fallback_decorator
    @retry_decorator
    @llm.call('litellm', **config['call'])
    @prompt_template(template)
    async def async_call_mirascope(**kwargs): ...
    
    return config, async_call_mirascope

async def async_stream_output_logfire(stream: AsyncIterator, logfire_metadata: dict, parse_objects=True) -> AsyncIterator[str]:
    """Public async interface for streaming output processing"""
    processor = AsyncStreamProcessor()
    
    async for result in processor.process_stream(stream, parse_objects=parse_objects):
        yield result

    if "LOGFIRE_TOKEN" in os.environ:
        if logfire_metadata is not None:
            logfire.info(
                processor.full_response,
                attributes=logfire_metadata,
            )

def mirascope_pipeline(prompt_path, metadata={}, **kwargs):
    config, mirascope_call = create_mirascope_call(prompt_path)
    stream = mirascope_call(**kwargs)

    logfire_metadata={
        'name':config['route']
    }

    logfire_metadata.update(metadata)

    output = stream_output_logfire(stream, logfire_metadata)
    return output

async def async_mirascope_pipeline(prompt_path, metadata={}, **kwargs):
    """Async version of the mirascope pipeline that processes prompts and streams output."""
    config, async_mirascope_call = await async_create_mirascope_call(prompt_path)
    stream = await async_mirascope_call(**kwargs)
    logfire_metadata = {
        'name': config['route']
    }
    logfire_metadata.update(metadata)
    output = async_stream_output_logfire(stream, logfire_metadata)
    return output

def create_prompt_route(
    router: APIRouter,
    prompt_path: str,
    route_path: str,
    methods: list = ["POST"],
    response_model: Any = None,
    include_in_schema: bool = True,
    **route_kwargs
):
    """
    Creates a FastAPI route that processes prompts using the mirascope pipeline.
    
    Args:
        router: FastAPI router instance
        prompt_path: Path to the prompt template file
        route_path: URL path for the endpoint
        methods: HTTP methods to support (default: ["POST"])
        response_model: Response model for OpenAPI docs
        include_in_schema: Whether to include in OpenAPI docs
        route_kwargs: Additional route parameters
    """
    
    async def endpoint_handler(request: Request):
        try:
            # Get input data from request
            input_data = await request.json()
            
            # Process the prompt pipeline
            output_stream = await async_mirascope_pipeline(
                prompt_path,
                metadata={"request": str(request)},
                **input_data
            )
            
            async def generate():
                async for chunk in output_stream:
                    yield chunk + "\n" 
            
            # Return streaming response
            return StreamingResponse(
                generate(),
                media_type="application/x-ndjson"
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error processing prompt: {str(e)}"
            )

    # Add the route to the router
    router.add_api_route(
        route_path,
        endpoint=endpoint_handler,
        methods=methods,
        response_model=response_model,
        include_in_schema=include_in_schema,
        **route_kwargs
    )

    return router