from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi_limiter.depends import RateLimiter
from passlib.context import CryptContext
from functools import wraps
import hashlib
import asyncio
import time
import json
import hmac
import os

API_TOKEN = os.environ["API_TOKEN"]
API_TOKEN_TIMEOUT = float(os.environ["API_TOKEN_TIMEOUT"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

from src.http.crytptography import token_auth

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

Authentication-Specific Usage:generate_auth_token
401 - Use for: Missing token, invalid token, expired token
403 - Use for: Valid token but insufficient permissions
429 - Use for: API rate limit violations
"""

## Http handler that enables decorating a route, with optionnal functionalities:
# - authentication : checks if the token is valid
# - rate limit : number of times a user can call the route per minute, use IP Adress

async def credit_refund_wrapper(generator, price, user_id):
    """
    A generator wrapper that catches exceptions and refunds credits.
    """
    try:
        async for item in generator:
            yield item
    except Exception as e:
        print(f"Streaming error for user {user_id}. Refunding {price} credits.", flush=True)
        # Refund the credits by deducting a negative amount
        await deduct_credits(-price, user_id)
        # Optionally, you can yield a final error message to the client
        error_message = json.dumps(
            {
                "format": "error",
                "content": f"A server error occurred. Your credits have been refunded. Error details: {str(e)}",
            }
        )

        yield error_message.encode("utf-8") + b"\n"
        # It's important to re-raise or handle the exception so the stream terminates correctly.
        # For this use case, we can just stop instead of raising.
        print(f"Original streaming error: {e}", flush=True)


def make_route(
    router,
    route,
    method="post",
    requires_auth=True,
    rate_limit=int(os.environ["RATE_LIMIT"]),
    rate_limit_seconds=int(os.environ["RATE_LIMIT_SECONDS"]),
):
    def route_decorator(func):

        token_dependency = None
        if requires_auth:
            token_dependency = Depends(oauth2_scheme)

        if method == "post":
            fastapi_decorator = router.post(
                route,
                # dependencies=[Depends(RateLimiter(times=rate_limit, seconds=rate_limit_seconds))],
            )
        elif method == "get":
            fastapi_decorator = router.get(
                route,
                # dependencies=[Depends(RateLimiter(times=rate_limit, seconds=rate_limit_seconds))]
            )
        elif method == "put":
            fastapi_decorator = router.put(
                route,
                # dependencies=[Depends(RateLimiter(times=rate_limit, seconds=rate_limit_seconds))]
            )
        elif method == "delete":
            fastapi_decorator = router.delete(
                route,
                # dependencies=[Depends(RateLimiter(times=rate_limit, seconds=rate_limit_seconds))]
            )
        else:
            raise ValueError("Invalid HTTP method specified")

        @fastapi_decorator
        @wraps(func)
        async def wrapped_function(*args, **kwargs):
            user_id = None  # Define user_id in the outer scope
            try:
                if requires_auth:
                    token = kwargs.get("token")
                    if token is None:
                        raise HTTPException(status_code=401, detail="Token is missing")
                    await token_auth(token)

                # Execute the actual endpoint function
                response = await func(*args, **kwargs)

                return response

            except HTTPException as http_exc:
                raise http_exc

            except Exception as e:
                print(f"An unexpected error occurred in route '{route}': {e}", flush=True)
                raise HTTPException(status_code=500, detail=f"An unexpected error occurred in route '{route}': {e}")

        return wrapped_function

    return route_decorator
