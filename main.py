import os
import string
import random
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl

from sqlalchemy import create_engine, Column, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable not set")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()


class URL(Base):
    __tablename__ = "urls"

    short_code = Column(String, primary_key=True, index=True)
    original_url = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))


Base.metadata.create_all(bind=engine)

app = FastAPI()


class URLRequest(BaseModel):
    url: HttpUrl


def generate_code(length=6):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/shorten")
def shorten(request: URLRequest):
    db = SessionLocal()

    short_code = generate_code()

    new_url = URL(
        short_code=short_code,
        original_url=str(request.url),
        created_at=datetime.now(timezone.utc),
    )

    db.add(new_url)
    db.commit()
    db.close()

    return {
        "short_url": f"/{short_code}",
        "original_url": str(request.url),
        "created_at": new_url.created_at.isoformat(),
    }


@app.get("/{code}")
def redirect(code: str):
    db = SessionLocal()

    url_entry = db.query(URL).filter(URL.short_code == code).first()

    if not url_entry:
        db.close()
        raise HTTPException(status_code=404, detail="Short code not found")

    db.close()
    return RedirectResponse(url=url_entry.original_url, status_code=307)


@app.get("/{code}/metadata")
def metadata(code: str):
    db = SessionLocal()

    url_entry = db.query(URL).filter(URL.short_code == code).first()

    if not url_entry:
        db.close()
        raise HTTPException(status_code=404, detail="Short code not found")

    response = {
        "short_code": url_entry.short_code,
        "original_url": url_entry.original_url,
        "created_at": url_entry.created_at.isoformat(),
    }

    db.close()
    return response