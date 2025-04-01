from fastapi import FastAPI, APIRouter
from src.mirascope import create_prompt_route
from dotenv import load_dotenv
from pathlib import Path
import os

app = FastAPI()
router = APIRouter()
load_dotenv()

def setup_prompt_routes():
    prompts_dir = Path(os.environ['PROMPT_PATH'])
    
    if not prompts_dir.exists():
        raise FileNotFoundError(f"Prompts directory not found at {prompts_dir.absolute()}")
    
    for prompt_file in prompts_dir.rglob("*.md"):
        relative_path = prompt_file.relative_to(prompts_dir)
        route_path = f"/{os.environ['APPLICATION_NAME']}/{relative_path.with_suffix('')}"
        create_prompt_route(
            router=router,
            prompt_path=str(prompt_file),
            route_path=route_path
        )
    
    app.include_router(router)

setup_prompt_routes()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=os.environ['PORT'])