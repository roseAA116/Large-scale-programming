from fastapi import Request
from fastapi.responses import JSONResponse


def _trace_id(request: Request) -> str | None:
    return getattr(request.state, "trace_id", None)


def ok(request: Request, data: object = None, *, status_code: int = 200) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "success": True,
            "data": data,
            "error": None,
            "trace_id": _trace_id(request),
        },
    )


def fail(
    request: Request,
    *,
    code: str,
    message: str,
    status_code: int,
    details: dict | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
            },
            "trace_id": _trace_id(request),
        },
    )

