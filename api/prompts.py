from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordBearer

from src.http.route_handler import make_route
from src.http.crytptography import token_auth

from clients.mirascope import async_mirascope_pipeline, load_prompt

from pydantic import BaseModel, create_model
from pathlib import Path
from typing import Any, List, Dict, AsyncGenerator, Callable
import json
import base64
import os

APPLICATION_NAME = os.getenv("APPLICATION_NAME")
API_BASE = f"/{APPLICATION_NAME}/v1/prompts"

prompt_router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

prompts_dir = Path(os.environ["PROMPT_PATH"])

def generate_pydantic_model(schema: Dict[str, Any], model_name: str):
    fields = {}
    for field_name, field_info in schema.items():
        field_type = eval(field_info["type"])
        if field_type == list:
            item_type = eval(field_info["description"].split("[")[1].split("]")[0])
            field_type = List[item_type]
        fields[field_name] = (field_type, ... if "description" in field_info else field_type)
    fields["user_id"] = (str, "i_am_not_authentified")
    fields["tool_calls"] = (List[str], None)
    return create_model(model_name, **fields)

def generate_docstring(description: str, schema: Dict[str, Any]):
    docstring_lines = [description]
    for field_name, field_info in schema.items():
        docstring_lines.append(f"    - **{field_name}**: {field_info['description']}")
    return "\n".join(docstring_lines)

class StreamResponse:
    @staticmethod
    async def generate(stream: AsyncGenerator, transform_fn: Callable = None):
        async for item in stream:
            try:
                if transform_fn:
                    item = transform_fn(item)
                yield json.dumps(item).encode() + b"\n"
            except Exception as e:
                print(e)

def create_endpoint_handler(prompt_file_path: str, route_path: str):
    config, _ = load_prompt(prompt_path=prompt_file_path)
    description = config["description"]
    schema = config["input_params"]
    InputSchema = generate_pydantic_model(schema, "InputSchema")
    docstring = generate_docstring(description, schema)

    async def endpoint_handler(request: InputSchema, token: str = Depends(oauth2_scheme)):
        await token_auth(token)
        input_data = request.dict()

        output_stream = await async_mirascope_pipeline(
            prompt_path=prompt_file_path,
            metadata={"request": str(request), "route": route_path},
            **input_data
        )

        return StreamingResponse(
            StreamResponse.generate(output_stream, transform_fn=None),
            media_type="application/x-ndjson"
        )

    endpoint_handler.__doc__ = docstring
    return endpoint_handler, config

for prompt_file in prompts_dir.rglob("*.md"):
    print(f"Loading prompt file: {prompt_file}")
    relative_path = prompt_file.relative_to(prompts_dir)
    route_path = f"{API_BASE}/{relative_path.with_suffix('')}"

    # Create a unique endpoint handler for each prompt file
    handler, config = create_endpoint_handler(prompt_file_path=str(prompt_file), route_path=route_path)

    price=0.0
    if "price" in config:
        price = float(config["price"])
    
    # Use make_route to add the route with consistent configuration
    make_route(
        router=prompt_router,
        route=route_path,
        method="post",
        requires_auth=True
    )(handler)