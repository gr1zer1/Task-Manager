from unittest.mock import AsyncMock

import pytest

from api_client import BaseApiClient, ServiceApiError


class DummyResponse:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload
        self.text = text
        self.content = b"" if payload is None else b"1"

    @property
    def is_error(self):
        return self.status_code >= 400

    def json(self):
        if self._payload is None:
            raise ValueError("No JSON body")
        return self._payload


@pytest.mark.asyncio
async def test_base_api_client_adds_bearer_token(monkeypatch):
    captured = {}

    async def fake_request(self, method, url, headers=None, **kwargs):
        captured["method"] = method
        captured["url"] = url
        captured["headers"] = headers
        return DummyResponse(payload={"ok": True})

    monkeypatch.setattr("httpx.AsyncClient.request", fake_request)

    result = await BaseApiClient("http://service")._request(
        "GET", "/resource", token="jwt-token"
    )

    assert result == {"ok": True}
    assert captured["headers"]["Authorization"] == "Bearer jwt-token"


@pytest.mark.asyncio
async def test_base_api_client_raises_service_error_with_detail(monkeypatch):
    async def fake_request(self, method, url, headers=None, **kwargs):
        return DummyResponse(status_code=404, payload={"detail": "Not found"})

    monkeypatch.setattr("httpx.AsyncClient.request", fake_request)

    with pytest.raises(ServiceApiError) as exc:
        await BaseApiClient("http://service")._request("GET", "/missing")

    assert exc.value.status_code == 404
    assert exc.value.detail == "Not found"
