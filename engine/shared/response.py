"""
Librarian API response envelope — applied to every /v1/* endpoint.

Shape:
    {
      "status": "ok",
      "data": { ... },
      "error": null
    }

    {
      "status": "error",
      "data": null,
      "error": {
        "code": "NOT_FOUND",
        "message": "Book not found"
      }
    }
"""

from typing import Generic, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class ApiError(BaseModel):
    """Structured error payload."""
    code: str
    message: str

    model_config = {"extra": "forbid"}


class ApiResponse(BaseModel, Generic[T]):
    """Generic envelope. FastAPI generates real OpenAPI types via T."""
    status: str  # "ok" | "error"
    data: Optional[T] = None
    error: Optional[ApiError] = None

    model_config = {"extra": "forbid"}


# Convenience constructors

def ok(data: T) -> ApiResponse[T]:
    """Build a success response."""
    return ApiResponse(status="ok", data=data)


def err(code: str, message: str) -> ApiResponse:
    """Build an error response."""
    return ApiResponse(
        status="error",
        error=ApiError(code=code, message=message),
    )


# Standard error codes
# Pattern: NOUN_VERB (e.g. BOOK_NOT_FOUND, CHUNK_NOT_FOUND)
# Matching Google AIP-193 style without the domain prefix.
ERROR_NOT_FOUND = "NOT_FOUND"
ERROR_INVALID_ARGUMENT = "INVALID_ARGUMENT"
ERROR_INTERNAL = "INTERNAL"
ERROR_ALREADY_EXISTS = "ALREADY_EXISTS"
ERROR_UNAUTHENTICATED = "UNAUTHENTICATED"
ERROR_PERMISSION_DENIED = "PERMISSION_DENIED"
