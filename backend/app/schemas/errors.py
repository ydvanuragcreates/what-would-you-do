"""Describes the error body in the OpenAPI docs (and so in the generated frontend types)."""

from pydantic import BaseModel


class FieldError(BaseModel):
    field: str
    message: str


class ErrorBody(BaseModel):
    code: str
    message: str
    details: list[FieldError] | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody
