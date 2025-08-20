from mirascope import llm, prompt_template
from mirascope.retries import FallbackError, fallback
from tenacity import RetryError, retry, stop_after_attempt, wait_exponential
from typing import Iterator, List, Dict, Any, Optional, Union, AsyncIterator

import logfire
import yaml
import json
import os
import re


from clients.logfire import app_log

## Mirascope is a library for building LLM applications.
# Here we provide helper to easily build task agents based on simple prompt file definitions.

## Tool importations
# from src.tools.calculator import square
# from src.tools.llm_planner import llm_planner
# from src.tools.retrieval import search_movie_bm25
from src.tools import *

def load_prompt(prompt_path):
    with open(prompt_path, "r") as f:
        prompt = f.read()

    prompt = prompt.split("\n---\n")
    config = prompt[0]

    template = [elt.strip() for elt in prompt[1:]]
    template = "\n\n".join(template)

    pattern = re.compile(r"```yaml(.*?)```", re.DOTALL)

    config = pattern.findall(config)[0]
    config = yaml.safe_load(config)

    ## If the model is defined in the env variables, replace it
    if "os.environ" in config["call"]["model"]:
        config["call"]["model"] = eval(config["call"]["model"])

    ## Replace string tools with function tools
    for i, tool in enumerate(config["call"]["tools"]):
        if isinstance(tool, str):
            config["call"]["tools"][i] = eval(tool)

    return config, template


async def async_load_prompt(prompt_path):
    with open(prompt_path, "r") as f:
        prompt = f.read()

    prompt = prompt.split("\n---\n")
    config = prompt[0]
    template = [elt.strip() for elt in prompt[1:]]
    template = "\n\n".join(template)

    pattern = re.compile(r"```yaml(.*?)```", re.DOTALL)

    config = pattern.findall(config)[0]
    config = yaml.safe_load(config)

    if "os.environ" in config["call"]["model"]:
        config["call"]["model"] = eval(config["call"]["model"])

    ## Replace string tools with function tools
    for i, tool in enumerate(config["call"]["tools"]):
        if isinstance(tool, str):
            config["call"]["tools"][i] = eval(tool)

    return config, template


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
                    yield json.dumps(parsed)
                except Exception as e:
                    yield "Error parsing content: " + str(e)


class AsyncYamlParser(AsyncContentParser):
    def __init__(self):
        super().__init__(r"```yaml(.*?)```")

    async def parse(self, content: str) -> Any:
        try:
            # Handle possible malformed YAML more gracefully
            content = content.strip()
            if not content.startswith(("{", "[")):  # If not JSON-like
                # Try to fix common YAML issues
                content = content.replace("\t", "  ")  # Convert tabs to spaces
                content = re.sub(r':\s*([^\s"\'\n]+)(\n|$)', r': "\1"\2', content)  # Quote unquoted values

            content = yaml.safe_load(content)
            return content
        except yaml.YAMLError as e:
            # Provide more detailed error information
            error_info = {
                "error": str(e),
                "problem_content": content,
                "advice": "Check YAML formatting - ensure proper indentation and quoting",
            }
            raise ValueError(json.dumps(error_info))


class AsyncJsonParser(AsyncContentParser):
    def __init__(self):
        super().__init__(r"```json(.*?)```")

    async def parse(self, content: str) -> Any:
        return json.loads(content)


class AsyncStreamProcessor:
    def __init__(self):
        self.parsers = [AsyncYamlParser(), AsyncJsonParser()]
        self.full_response = ""

    async def process_stream(self, stream: AsyncIterator, parse_objects=True) -> AsyncIterator[str]:
        """Process a stream of chunks asynchronously and yield parsed content as JSON strings"""
        async for chunk, tool in stream:
            if tool:
                result = await tool.call()

                result = f"""<tool_call>
### NAME: {tool.tool_call.function.name}
### ARGUMENTS: {tool.tool_call.function.arguments}
### RESULT: {result}
</tool_call>"""

                ## Replace '{' and '}' to avoid parsing issues
                result = result.replace("{", "(").replace("}", ")")

                self.full_response += result

                yield {"content": result, "format": "tool"}
            else:
                self.full_response += chunk.content

                if parse_objects:
                    async for result in self._process_content():
                        # print(result)
                        yield {"content": result, "format": "object"}

                yield {"content": chunk.content, "format": "text"}

    async def _process_content(self) -> AsyncIterator[str]:
        """Process the accumulated content through all parsers asynchronously"""
        for parser in self.parsers:
            async for result in parser.process(self.full_response):
                yield result


def dummy_decorator(func):
    return func


async def async_create_mirascope_call(prompt_path, tool_calls: list = None):

    config, template = await async_load_prompt(prompt_path)
    retry_decorator = dummy_decorator
    fallback_decorator = dummy_decorator

    ## If tool calls are provided, add them to the template
    if tool_calls:
        for tool_call in tool_calls:
            template += f"\n\nASSISTANT\n{tool_call}"

    if "retry" in config:
        retry_decorator = retry(
            stop=stop_after_attempt(config["retry"]), wait=wait_exponential(multiplier=1, min=4, max=10)
        )

    if "fallback" in config:
        fallback_decorator = fallback(
            RetryError, [{"catch": RetryError, "provider": "litellm", "model": config["fallback"]}]
        )

    @fallback_decorator
    @retry_decorator
    @llm.call("litellm", **config["call"])
    @prompt_template(template)
    async def async_call_mirascope(**kwargs): ...

    return config, async_call_mirascope


async def async_stream_output_logfire(prompt_path, metadata={}, **kwargs):
    processor = AsyncStreamProcessor()

    ## Make first call
    config, async_mirascope_call = await async_create_mirascope_call(prompt_path, tool_calls=[])

    parse_objects = True
    if "parse_objects" in config:
        parse_objects = config["parse_objects"]

    stream = await async_mirascope_call(**kwargs)
    tool_calls = []

    async for result in processor.process_stream(stream, parse_objects=parse_objects):
        try:
            if result["format"] == "tool":
                tool_calls.append(result["content"])
        except:
            pass
        yield result

    ## Handle tool call recursion
    n_tools = 0

    if "tool_recursion_depth" in config:
        tool_recursion_depth = config["tool_recursion_depth"]
    else:
        tool_recursion_depth = os.environ["TOOL_RECURSION_DEPTH"]

    while True:
        if len(tool_calls) <= n_tools:
            break
        elif n_tools < len(tool_calls):
            if tool_recursion_depth <= 0:
                break
            else:
                n_tools = len(tool_calls)
                tool_recursion_depth -= 1
                config, async_mirascope_call = await async_create_mirascope_call(prompt_path, tool_calls=tool_calls)
                stream = await async_mirascope_call(**kwargs)

                async for result in processor.process_stream(stream, parse_objects=parse_objects):
                    try:
                        if result["format"] == "tool":
                            tool_calls.append(result["content"])
                    except:
                        pass
                    yield result

    ## Update metadata and log to logfire
    logfire_metadata = metadata

    tags = []
    if "tags" in config:
        tags = config["tags"]

    logfire_metadata.update(config)

    logfire_metadata["reply"] = processor.full_response

    app_log(
        level="info",
        message=prompt_path,
        attributes=logfire_metadata,
        tags=tags,
    )


async def async_mirascope_pipeline(prompt_path, metadata={}, **kwargs):
    """Async version of the mirascope pipeline that processes prompts and streams output."""
    output = async_stream_output_logfire(prompt_path, metadata={}, **kwargs)
    return output
