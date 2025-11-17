from biotoolsllmannotate.io.biotools_api import (
    fetch_biotools_entry,
    validate_biotools_entry,
)
import types


class DummyResp:
    def __init__(self, status_code=200, json_data=None, text="OK"):
        self.status_code = status_code
        self._json = json_data or {}
        self.text = text

    def json(self):
        return self._json


def test_fetch_biotools_entry_adds_auth_header(monkeypatch):
    captured = {}

    def fake_get(url, headers=None, timeout=10):
        captured["url"] = url
        captured["headers"] = headers
        return DummyResp(status_code=404)  # ensure function returns None

    monkeypatch.setattr("requests.get", fake_get)
    result = fetch_biotools_entry(
        "toolX", api_base="https://example.org/api/tool/", token="TOKEN123"
    )
    assert result is None
    assert captured["headers"]["Authorization"] == "Token TOKEN123"
    assert captured["headers"]["Accept"] == "application/json"
    assert captured["url"].endswith("/toolX?format=json")


def test_validate_biotools_entry_adds_auth_header_valid(monkeypatch):
    captured = {}

    def fake_post(url, json=None, headers=None, timeout=30):
        captured["url"] = url
        captured["json"] = json
        captured["headers"] = headers
        return DummyResp(status_code=200)

    monkeypatch.setattr("requests.post", fake_post)
    entry = {"name": "x", "description": "d", "homepage": "http://h"}
    res = validate_biotools_entry(
        entry, api_base="https://example.org/api/tool/validate/", token="T1"
    )
    assert res["valid"] is True
    assert captured["headers"]["Authorization"] == "Token T1"
    assert captured["headers"]["Content-Type"] == "application/json"


def test_validate_biotools_entry_parses_errors(monkeypatch):
    def fake_post(url, json=None, headers=None, timeout=30):
        return DummyResp(
            status_code=400, json_data={"errors": ["name: This field is required"]}
        )

    monkeypatch.setattr("requests.post", fake_post)
    entry = {"description": "only"}
    res = validate_biotools_entry(entry)
    assert res["valid"] is False
    assert any("name" in e for e in res["errors"])


def test_validate_biotools_entry_timeout(monkeypatch):
    class TimeoutExc(Exception):
        pass

    def fake_post(url, json=None, headers=None, timeout=30):
        raise TimeoutExc("timeout")

    monkeypatch.setattr("requests.post", fake_post)
    entry = {"name": "x", "description": "d", "homepage": "http://h"}
    res = validate_biotools_entry(entry)
    assert res["valid"] is False
    assert (
        "timed out" in res["errors"][0].lower() or "timeout" in res["errors"][0].lower()
    )
