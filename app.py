from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi import FastAPI

# import redis.asyncio as redis
import dotenv
dotenv.load_dotenv()

# from fastapi_limiter import FastAPILimiter

from api.prompts import prompt_router

app = FastAPI()

## Rate limiting based on IP address, uses a local non persistent redis server
# @app.on_event("startup")
# async def startup():
#     redis_connection = redis.from_url("redis://localhost:3500", encoding="utf-8", decode_responses=True)
#     await FastAPILimiter.init(redis_connection)

# Add middleware to handle CORS policy (to be adapted once we know the origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,  # Allow credentials
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

app.include_router(prompt_router)  ## include prompt router

if __name__ == "__main__":
    # Run the FastAPI application using uvicorn
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)  # Run the app on the specified port
