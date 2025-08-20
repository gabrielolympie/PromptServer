import aiohttp
import requests
import base64
import asyncio
import json
import os

from src.http.crytptography import generate_auth_token, async_generate_auth_token
from src.utils.parallelism import pmap


class PromptClient:
    def __init__(self, base_url=None, api_key=None):
        if base_url:
            self.base_url = base_url
        else:
            self.base_url = f"{os.getenv('BASE_URL')}/{os.getenv('APPLICATION_NAME')}/v1"
        
        if api_key:
            self.api_key = api_key
        else:
            self.api_key = os.getenv('API_TOKEN')
            
    def generate_header(self):
        return generate_auth_token(self.api_key)
    
    def stream(
        self,
        input_data,
        route,
        method='post'
    ):
        buffer = ""
        response = requests.post(f"{self.base_url}{route}", json=input_data, stream=True, headers=self.generate_header())
        
        for chunk in response.iter_content(chunk_size=None):
            if chunk:
                decoded_chunk = chunk.decode("utf-8")
                buffer += decoded_chunk

                while True:
                    try:
                        end_pos = buffer.index("\n") if "\n" in buffer else -1
                        if end_pos == -1:
                            break

                        json_str = buffer[:end_pos]
                        buffer = buffer[end_pos + 1 :]

                        if json_str.strip():
                            data = json.loads(json_str)
                            yield data

                    except (json.JSONDecodeError, ValueError):
                        break
                    
    def call(
        self,
        input_data,
        route,
        method="post"
    ):
        response = self.stream(input_data, route, method)
        
        text, objects, tools = [], [], []

        for obj in response:
            if obj["format"] == "text":
                text.append(obj["content"])
            elif obj["format"] == "object":
                objects.append(obj["content"])
            elif obj["format"] == "tool":
                tools.append(obj["content"])

        return "".join(text), objects, tools


    def batch(
        self,
        input_data,
        route,
        n_jobs=4,
        verbose=50,
        method='post'
    ):
        batch = [{"input_data": kwargs, "route": route, "method": method} for kwargs in input_data]
        return pmap(self.call, batch, n_jobs=n_jobs, verbose=verbose)

    async def astream(self, input_data, route, method='post'):
        buffer = ""
        headers = self.generate_header()
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.base_url}{route}", json=input_data, headers=headers) as response:
                async for chunk in response.content:
                    if chunk:
                        decoded_chunk = chunk.decode("utf-8")
                        buffer += decoded_chunk

                        while True:
                            try:
                                end_pos = buffer.index("\n") if "\n" in buffer else -1
                                if end_pos == -1:
                                    break

                                json_str = buffer[:end_pos]
                                buffer = buffer[end_pos + 1:]

                                if json_str.strip():
                                    data = json.loads(json_str)
                                    yield data

                            except (json.JSONDecodeError, ValueError):
                                break

    async def acall(self, input_data, route, method="post"):
        text, objects, tools = [], [], []
        
        async for obj in self.astream(input_data, route, method):
            if obj["format"] == "text":
                text.append(obj["content"])
            elif obj["format"] == "object":
                objects.append(obj["content"])
            elif obj["format"] == "tool":
                tools.append(obj["content"])

        return "".join(text), objects, tools

    async def abatch(self, input_data, route, n_jobs=4, verbose=50, method='post'):
        # Create tasks for all input data
        tasks = []
        async with aiohttp.ClientSession() as session:
            for kwargs in input_data:
                task = asyncio.create_task(self.acall(kwargs, route, method))
                tasks.append(task)
            
            # Execute tasks concurrently
            results = await asyncio.gather(*tasks)
            return results