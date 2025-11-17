"""Test bio.tools schema validation for payloads."""

from biotoolsllmannotate.schema.models import BioToolsEntry
from pydantic import ValidationError
import pytest


def test_valid_minimal_entry():
    """Test that a minimal valid entry passes validation."""
    entry = {
        "name": "TestTool",
        "description": "A test bioinformatics tool",
        "homepage": "https://example.com/testtool",
    }
    # Should not raise
    validated = BioToolsEntry(**entry)
    assert validated.name == "TestTool"
    assert validated.description == "A test bioinformatics tool"
    assert validated.homepage == "https://example.com/testtool"


def test_valid_entry_with_biotoolsid():
    """Test that an entry with biotoolsID passes validation."""
    entry = {
        "name": "TestTool",
        "description": "A test tool",
        "homepage": "https://example.com",
        "biotoolsID": "testtool",
    }
    validated = BioToolsEntry(**entry)
    assert validated.biotoolsID == "testtool"


def test_valid_entry_with_topics():
    """Test that an entry with topics passes validation."""
    entry = {
        "name": "TestTool",
        "description": "A test tool",
        "homepage": "https://example.com",
        "biotoolsID": "testtool",
        "topic": [
            {"term": "Genomics", "uri": "http://edamontology.org/topic_0622"},
            {"term": "RNA-Seq", "uri": "http://edamontology.org/topic_3170"},
        ],
    }
    validated = BioToolsEntry(**entry)
    assert len(validated.topic) == 2
    assert validated.topic[0].term == "Genomics"


def test_invalid_entry_missing_name():
    """Test that an entry without name fails validation."""
    entry = {
        "description": "A test tool",
        "homepage": "https://example.com",
    }
    with pytest.raises(ValidationError) as exc_info:
        BioToolsEntry(**entry)
    errors = exc_info.value.errors()
    assert any(e["loc"] == ("name",) for e in errors)


def test_invalid_entry_missing_description():
    """Test that an entry without description fails validation."""
    entry = {
        "name": "TestTool",
        "homepage": "https://example.com",
    }
    with pytest.raises(ValidationError) as exc_info:
        BioToolsEntry(**entry)
    errors = exc_info.value.errors()
    assert any(e["loc"] == ("description",) for e in errors)


def test_invalid_entry_missing_homepage():
    """Test that an entry without homepage fails validation."""
    entry = {
        "name": "TestTool",
        "description": "A test tool",
    }
    with pytest.raises(ValidationError) as exc_info:
        BioToolsEntry(**entry)
    errors = exc_info.value.errors()
    assert any(e["loc"] == ("homepage",) for e in errors)


def test_invalid_entry_all_required_missing():
    """Test that an entry missing all required fields fails validation."""
    entry = {"biotoolsID": "testtool"}
    with pytest.raises(ValidationError) as exc_info:
        BioToolsEntry(**entry)
    errors = exc_info.value.errors()
    # Should have errors for name, description, and homepage
    error_fields = {e["loc"][0] for e in errors}
    assert "name" in error_fields
    assert "description" in error_fields
    assert "homepage" in error_fields


def test_valid_entry_with_documentation():
    """Test that an entry with documentation passes validation."""
    entry = {
        "name": "TestTool",
        "description": "A test tool",
        "homepage": "https://example.com",
        "documentation": [
            {"url": "https://example.com/docs", "type": ["Manual"]},
            {"url": "https://example.com/api", "type": ["API documentation"]},
        ],
    }
    validated = BioToolsEntry(**entry)
    assert len(validated.documentation) == 2
    assert validated.documentation[0].url == "https://example.com/docs"


def test_valid_entry_with_links():
    """Test that an entry with links passes validation."""
    entry = {
        "name": "TestTool",
        "description": "A test tool",
        "homepage": "https://example.com",
        "link": [
            {"url": "https://github.com/test/tool", "type": ["Repository"]},
            {"url": "https://example.com", "type": ["Homepage"]},
        ],
    }
    validated = BioToolsEntry(**entry)
    assert len(validated.link) == 2
