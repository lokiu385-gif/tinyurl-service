from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_shorten_redirect_metadata_flow():
    r = client.post("/shorten", json={"url": "https://example.com"})
    assert r.status_code == 200
    body = r.json()

    # normalize trailing slash
    assert body["original_url"].rstrip("/") == "https://example.com"

    code = body["short_url"].rstrip("/").split("/")[-1]

    r = client.get(f"/{code}", follow_redirects=False)
    assert r.status_code in (307, 308)
    assert r.headers["location"].rstrip("/") == "https://example.com"

    r = client.get(f"/{code}/metadata")
    assert r.status_code == 200
    meta = r.json()
    assert meta["short_code"] == code
    assert meta["original_url"].rstrip("/") == "https://example.com"