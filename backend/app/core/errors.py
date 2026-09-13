from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class DomainError(Exception):
    status_code = 400
    code = "DOMAIN_ERROR"
    message = "Request could not be completed"


class NotFound(DomainError):
    status_code, code, message = 404, "NOT_FOUND", "Resource not found"


class Conflict(DomainError):
    status_code, code, message = 409, "CONFLICT", "Resource changed or conflicts with this request"


class Unauthorized(DomainError):
    status_code, code, message = 401, "UNAUTHORIZED", "Authentication required"


class Forbidden(DomainError):
    status_code, code, message = 403, "FORBIDDEN", "Access denied"


class ValidationIssue(DomainError):
    status_code, code, message = 422, "VALIDATION_ERROR", "Request validation failed"


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def domain_error(_request: Request, exc: DomainError):
        return JSONResponse(status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}})

    @app.exception_handler(RequestValidationError)
    async def validation_error(_request: Request, _exc: RequestValidationError):
        # Never echo raw request input: future requests may contain credentials.
        return JSONResponse(status_code=422, content={"error": {
            "code": "VALIDATION_ERROR", "message": "Request validation failed"}})
