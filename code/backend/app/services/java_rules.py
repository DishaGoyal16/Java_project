"""Internal Java adapter. Original persistence and public API stay unchanged."""
import json
import os
import logging
from urllib.request import Request, urlopen
from urllib.parse import urlencode, urlparse
from urllib.error import HTTPError, URLError
from fastapi import HTTPException

def enabled(operation="workflow"):
    mode = os.getenv("SCMS_RULES_ENGINE", "python")
    if mode not in ("python", "java"):
        raise RuntimeError("SCMS_RULES_ENGINE must be python or java")
    if os.getenv("SCMS_RULES_DIAGNOSTICS", "").lower() == "true":
        logging.getLogger("uvicorn.error").info("SCMS operation=%s engine=%s automatic_fallback=false", operation, mode)
    return mode == "java"

def call(operation, values):
    base = os.getenv("SCMS_RULES_URL", "http://127.0.0.1:8091")
    parsed = urlparse(base)
    if parsed.scheme != "http" or parsed.hostname not in ("127.0.0.1", "localhost"):
        raise RuntimeError("Java rules must use a loopback HTTP URL")
    token = os.environ.get("SCMS_RULES_TOKEN", "")
    if len(token) < 32:
        raise RuntimeError("SCMS_RULES_TOKEN must have at least 32 characters")
    data = {k: str(v).lower() if isinstance(v, bool) else str(v) for k,v in values.items()}
    request = Request(base + "/internal/" + operation, data=urlencode(data).encode(),
                      headers={"Authorization": "Bearer " + token,
                               "Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urlopen(request, timeout=5) as response:
            return json.load(response)
    except HTTPError as ex:
        if ex.code in (400,403,404,409):
            detail = json.load(ex).get("error", {})
            if detail.get("code") != "INVALID_RULE_INPUT":
                raise HTTPException(status_code=ex.code, detail=detail) from None
        raise HTTPException(503, detail={"code":"RULES_UNAVAILABLE", "message":"Rules service unavailable."}) from None
    except (URLError, TimeoutError, ValueError, OSError):
        raise HTTPException(503, detail={"code":"RULES_UNAVAILABLE", "message":"Rules service unavailable."}) from None
