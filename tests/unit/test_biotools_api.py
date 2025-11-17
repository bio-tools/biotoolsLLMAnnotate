import pytest
from biotoolsllmannotate.io.biotools_api import fetch_biotools_entry

import requests


def test_fetch_biotools_entry_found(monkeypatch):
    class FakeResp:
        status_code = 200

        def json(self):
            return {"name": "TestTool", "status": "active", "description": "desc"}

    def fake_get(url, headers, timeout):
        return FakeResp()

    monkeypatch.setattr(requests, "get", fake_get)
    result = fetch_biotools_entry("testid")
    assert result == {"name": "TestTool", "status": "active", "description": "desc"}
    assert result["status"] == "active"


def test_fetch_biotools_entry_not_found(monkeypatch):
    class FakeResp:
        status_code = 404

        def json(self):
            return {}

    def fake_get(url, headers, timeout):
        return FakeResp()

    monkeypatch.setattr(requests, "get", fake_get)
    result = fetch_biotools_entry("missingid")
    assert result is None


def test_fetch_biotools_entry_error(monkeypatch):
    def fake_get(url, timeout):
        raise requests.RequestException("fail")

    monkeypatch.setattr(requests, "get", fake_get)
    with pytest.raises(RuntimeError):
        fetch_biotools_entry("errid")
