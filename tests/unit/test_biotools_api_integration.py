"""Integration test for bio.tools API with mock dev server responses."""

from biotoolsllmannotate.io.biotools_api import (
    validate_biotools_entry,
    fetch_biotools_entry,
)


class MockResponse:
    """Minimal mock for requests.Response."""

    def __init__(self, status_code, json_data=None, text=""):
        self.status_code = status_code
        self._json_data = json_data or {}
        self.text = text

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if 400 <= self.status_code < 600:
            raise RuntimeError(f"HTTP {self.status_code}")


def test_validate_entry_dev_server_success(monkeypatch):
    """Simulate a successful validation response from dev server."""

    def mock_post(url, json=None, headers=None, timeout=30):
        # Verify auth header present
        assert headers.get("Authorization") == "Token dev123"
        assert "bio-tools-dev.sdu.dk" in url
        return MockResponse(200)

    monkeypatch.setattr("requests.post", mock_post)

    entry = {
        "name": "TestTool",
        "description": "A test tool",
        "homepage": "https://example.org",
        "biotoolsID": "testtool",
    }
    result = validate_biotools_entry(
        entry,
        api_base="https://bio-tools-dev.sdu.dk/api/tool/validate/",
        token="dev123",
    )
    assert result["valid"] is True
    assert result["errors"] == []


def test_validate_entry_dev_server_error(monkeypatch):
    """Simulate a validation error from dev server."""

    def mock_post(url, json=None, headers=None, timeout=30):
        return MockResponse(
            400,
            json_data={
                "name": ["This field is required"],
                "homepage": ["Enter a valid URL"],
            },
        )

    monkeypatch.setattr("requests.post", mock_post)

    entry = {"description": "incomplete"}
    result = validate_biotools_entry(entry, token="dev123")
    assert result["valid"] is False
    assert len(result["errors"]) > 0
    assert any("name" in e.lower() for e in result["errors"])


def test_fetch_entry_dev_server_found(monkeypatch):
    """Simulate fetching an existing tool from dev server."""

    def mock_get(url, headers=None, timeout=10):
        assert headers.get("Authorization") == "Token dev456"
        return MockResponse(
            200,
            json_data={
                "name": "ExistingTool",
                "biotoolsID": "existingtool",
                "homepage": "https://tool.example.org",
            },
        )

    monkeypatch.setattr("requests.get", mock_get)

    result = fetch_biotools_entry(
        "existingtool",
        api_base="https://bio-tools-dev.sdu.dk/api/tool/",
        token="dev456",
    )
    assert result is not None
    assert result["name"] == "ExistingTool"


def test_fetch_entry_dev_server_not_found(monkeypatch):
    """Simulate 404 response from dev server."""

    def mock_get(url, headers=None, timeout=10):
        return MockResponse(404, text="Not found")

    monkeypatch.setattr("requests.get", mock_get)

    result = fetch_biotools_entry(
        "nonexistent", api_base="https://bio-tools-dev.sdu.dk/api/tool/", token="dev789"
    )
    assert result is None


def test_validate_entry_dev_server_auth_failure(monkeypatch):
    """Simulate 401 authentication failure from dev server."""

    def mock_post(url, json=None, headers=None, timeout=30):
        return MockResponse(
            401,
            json_data={"detail": "Authentication credentials were not provided."},
            text="Unauthorized",
        )

    monkeypatch.setattr("requests.post", mock_post)

    entry = {"name": "Tool", "description": "desc", "homepage": "https://x.org"}
    result = validate_biotools_entry(entry, token=None)  # No token
    assert result["valid"] is False
    assert any("401" in e for e in result["errors"])
