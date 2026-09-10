"""FastAPI app: error envelope, CORS, router registration."""

import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.config import CORS_ORIGINS
from app.routers import auth, photos, rooms, search, spaces

logger = logging.getLogger(__name__)

app = FastAPI(title="SpaceMatch API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(spaces.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(rooms.router, prefix="/api")
app.include_router(photos.router, prefix="/api")


# --- Error envelope --------------------------------------------------------
#
# The API contract requires every error to be {"error": "string"}. FastAPI's
# defaults use {"detail": ...} and a 422 for validation failures — these
# handlers make every error path conform, so routers never format errors
# themselves.


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # exc.headers carries Retry-After on 429s — dropping it would leave clients
    # with no idea when to come back.
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": str(exc.detail)},
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def request_validation_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    message = errors[0]["msg"] if errors else "validation error"
    return JSONResponse(status_code=400, content={"error": message})


@app.exception_handler(ValidationError)
async def pydantic_validation_handler(request: Request, exc: ValidationError):
    errors = exc.errors()
    message = errors[0]["msg"] if errors else "validation error"
    return JSONResponse(status_code=400, content={"error": message})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"error": "internal server error"})
