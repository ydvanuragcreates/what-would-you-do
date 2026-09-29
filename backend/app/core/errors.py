"""Domain errors and how they become HTTP responses.

Services raise these; they know nothing about HTTP. One handler (see
`register_error_handlers`) turns them into a consistent JSON body:

    {"error": {"code": "invalid_credentials", "message": "Invalid email or password."}}
"""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class AppError(Exception):
    status_code = 500
    code = "internal_error"
    message = "Something went wrong."

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.message
        super().__init__(self.message)


class NotAuthenticatedError(AppError):
    status_code = 401
    code = "not_authenticated"
    message = "You need to log in."


class InvalidCredentialsError(AppError):
    status_code = 401
    code = "invalid_credentials"
    # Deliberately identical for "no such user" and "wrong password".
    message = "Invalid email or password."


class AccountExistsError(AppError):
    status_code = 409
    code = "account_exists"
    message = "That username or email is already registered."


class RateLimitedError(AppError):
    status_code = 429
    code = "rate_limited"
    message = "Too many attempts. Please wait a moment and try again."

    def __init__(self, retry_after_seconds: int) -> None:
        super().__init__()
        self.retry_after_seconds = retry_after_seconds


class RoundNotFoundError(AppError):
    status_code = 404
    code = "round_not_found"
    message = "That round doesn't exist."


class RoundNotCompletedError(AppError):
    status_code = 409
    code = "round_not_completed"
    message = "Finish the round to see your result."


class NotEnoughScenariosError(AppError):
    status_code = 409
    code = "not_enough_scenarios"
    message = "There aren't enough scenarios to start a round yet."


class RoundNotInProgressError(AppError):
    status_code = 409
    code = "round_not_in_progress"
    message = "This round has already finished."


class NotCurrentQuestionError(AppError):
    status_code = 409
    code = "not_current_question"
    message = "That isn't the current question for this round."


class InvalidChoiceError(AppError):
    status_code = 400
    code = "invalid_choice"
    message = "That choice doesn't belong to this question."


def _error_response(
    status_code: int,
    code: str,
    message: str,
    details: list[dict[str, str]] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    body: dict[str, object] = {"code": code, "message": message}
    if details:
        body["details"] = details
    return JSONResponse({"error": body}, status_code=status_code, headers=headers)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, error: AppError) -> JSONResponse:
        headers = None
        if isinstance(error, RateLimitedError):
            headers = {"Retry-After": str(error.retry_after_seconds)}
        return _error_response(error.status_code, error.code, error.message, headers=headers)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, error: RequestValidationError
    ) -> JSONResponse:
        # Only field and message. FastAPI's default body also echoes the submitted
        # value ("input"), which would send a rejected password straight back.
        details = [
            {
                "field": ".".join(str(part) for part in e["loc"][1:]),
                "message": e["msg"].removeprefix("Value error, "),
            }
            for e in error.errors()
        ]
        return _error_response(422, "validation_error", "Some fields are invalid.", details)

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, error: Exception) -> JSONResponse:
        # Log the real cause for us; tell the client nothing about the internals.
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return _error_response(500, "internal_error", "Something went wrong.")
