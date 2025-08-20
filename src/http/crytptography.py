from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from functools import wraps
import hashlib
import time
import hmac
import os

API_TOKEN = os.environ["API_TOKEN"]
API_TOKEN_TIMEOUT = float(os.environ["API_TOKEN_TIMEOUT"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

"""
HTTP Status Codes Reference:
200 - OK: Standard success response for GET, PUT, and PATCH requests
201 - Created: Resource successfully created (POST requests)
202 - Accepted: Request accepted but processing not yet complete
204 - No Content: Success with no response body (DELETE requests)
400 - Bad Request: Invalid syntax, missing fields, or malformed data
401 - Unauthorized: Missing or invalid authentication credentials
403 - Forbidden: Authenticated but insufficient permissions
404 - Not Found: Requested resource doesn't exist
405 - Method Not Allowed: Invalid HTTP method for endpoint
406 - Not Acceptable: Unsupported content type in Accept header
409 - Conflict: Request conflicts with current server state
410 - Gone: Resource permanently unavailable (no redirect)
413 - Payload Too Large: Request body exceeds size limits
415 - Unsupported Media Type: Invalid Content-Type header
422 - Unprocessable Entity: Semantic validation errors
429 - Too Many Requests: Rate limit exceeded
500 - Internal Server Error: Generic server-side failure
501 - Not Implemented: Endpoint exists but isn't implemented
502 - Bad Gateway: Invalid response from upstream server
503 - Service Unavailable: Server temporarily overloaded/maintenance
504 - Gateway Timeout: Upstream server timeout

Authentication-Specific Usage:
401 - Use for: Missing token, invalid token, expired token
403 - Use for: Valid token but insufficient permissions
429 - Use for: API rate limit violations
"""


def generate_hash(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()


def generate_auth_token(api_key=None):
    if api_key is None:
        api_key = os.getenv("API_TOKEN")
    timestamp = int(time.time())
    message = f"{api_key}:{timestamp}"
    signature = hmac.new(api_key.encode(), message.encode(), hashlib.sha256).hexdigest()
    return {"Authorization": f"Bearer {timestamp}:{signature}"}


async def async_generate_auth_token():
    api_key = os.getenv("API_TOKEN")
    timestamp = int(time.time())
    message = f"{api_key}:{timestamp}"
    signature = hmac.new(api_key.encode(), message.encode(), hashlib.sha256).hexdigest()
    return {"Authorization": f"Bearer {timestamp}:{signature}"}


## Token verification system
async def token_auth(token: str, API_TOKEN: str = API_TOKEN, API_TOKEN_TIMEOUT: float = API_TOKEN_TIMEOUT):
    try:
        auth_parts = token.split(":")

        if len(auth_parts) != 2:
            raise HTTPException(status_code=401, detail="Invalid token format, expected format: timestamp:signature")

        timestamp, client_signature = auth_parts

        current_time = int(time.time())
        if current_time - int(timestamp) > API_TOKEN_TIMEOUT:
            raise HTTPException(status_code=401, detail="Token has expired, please generate a new one")

        message = f"{API_TOKEN}:{timestamp}"
        expected_signature = hmac.new(API_TOKEN.encode(), message.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(client_signature, expected_signature):
            raise HTTPException(status_code=401, detail="Invalid token signature")

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
