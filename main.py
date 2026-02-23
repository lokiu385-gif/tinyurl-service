from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl
from datetime import datetime
import secrets
import string
import re

app = FastAPI(title="TinyURL Service")

# In-memory storage (resets on restart)
db: dict[str, dict] = {}

# Prevent collisions with real endpoints / FastAPI docs
RESERVED_ALIASES = {
    "health",
    "docs",
    "redoc",
    "openapi.json",
    "shorten",
}

ALIAS_RE = re.compile(r"^[A-Za-z0-9_-]{1,30}$")


class URLRequest(BaseModel):
    url: HttpUrl
    custom_alias: str | None = None


def generate_code(length: int = 6) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/shorten")
def shorten_url(payload: URLRequest, request: Request):
    # Decide code
    if payload.custom_alias:
        code = payload.custom_alias.strip()

        if code.lower() in RESERVED_ALIASES:
            raise HTTPException(status_code=400, detail="Alias is reserved")

        if not ALIAS_RE.match(code):
            raise HTTPException(
                status_code=400,
                detail="Invalid alias (use 1-30 chars: letters, digits, _ or -)",
            )

        if code in db:
            raise HTTPException(status_code=409, detail="Alias already exists")
    else:
        code = generate_code()
        while code in db:
            code = generate_code()

    created_at = datetime.utcnow().isoformat() + "Z"
    db[code] = {
        "original_url": str(payload.url),
        "short_code": code,
        "created_at": created_at,
    }

    base = str(request.base_url).rstrip("/")  # works locally + when deployed
    return {
        "short_url": f"{base}/{code}",
        "original_url": str(payload.url),
        "created_at": created_at,
    }


@app.get("/{code}/metadata")
def get_metadata(code: str):
    if code not in db:
        raise HTTPException(status_code=404, detail="Short code not found")
    return db[code]


@app.get("/{code}")
def redirect(code: str):
    if code not in db:
        raise HTTPException(status_code=404, detail="Short code not found")
    return RedirectResponse(url=db[code]["original_url"], status_code=307)