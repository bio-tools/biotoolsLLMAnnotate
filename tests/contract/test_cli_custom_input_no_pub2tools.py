"""
Test that when custom_pub2tools_biotools_json is set, pub2tools CLI is never invoked.
"""

import json
from pathlib import Path
from unittest.mock import patch
import pytest


def test_custom_input_empty_file_does_not_invoke_pub2tools(tmp_path):
    """
    When custom_pub2tools_biotools_json points to an empty file,
    pub2tools should still NOT be invoked (even though no candidates were loaded).
    This is the critical test - it ensures has_explicit_input prevents pub2tools.
    """
    from biotoolsllmannotate.cli.run import execute_run

    # Create empty custom input file
    input_file = tmp_path / "empty_input.json"
    input_file.write_text("[]")

    # Mock pub2tools to ensure it's never called
    with patch(
        "biotoolsllmannotate.ingest.pub2tools_client.fetch_via_cli"
    ) as mock_fetch:
        mock_fetch.return_value = []

        with patch(
            "biotoolsllmannotate.cli.run.load_registry_from_pub2tools"
        ) as mock_registry:
            mock_registry.return_value = None

            config_data = {
                "pipeline": {
                    "custom_pub2tools_biotools_json": str(input_file),
                    "from_date": "2025-01-01",
                    "to_date": "2025-01-02",
                    "bio_add_threshold": 0.7,
                    "bio_review_threshold": 0.5,
                    "doc_add_threshold": 0.5,
                    "doc_review_threshold": 0.3,
                    "limit": None,
                    "concurrency": 1,
                    "enrich_europe_pmc": False,
                    "enrich_homepage": False,
                    "offline": False,
                    "dry_run": True,
                },
                "ollama": {
                    "api_url": "http://localhost:11434",
                    "model": "test-model",
                    "model_params": {
                        "temperature": 0.1,
                        "top_p": 0.9,
                    },
                },
                "logging": {},
            }

            output_root = tmp_path / "out"

            try:
                execute_run(
                    config_data=config_data,
                    base_output_root=output_root,
                    output=None,
                    report=None,
                    updated_entries=None,
                    enriched_cache=None,
                    registry_path=None,
                    resume_from_pub2tools=False,
                    resume_from_enriched=False,
                    resume_from_scoring=False,
                    offline=False,
                    dry_run=True,
                    validate_biotools_api=False,
                )
            except Exception as e:
                pass

            # Critical check: pub2tools should NOT be called even though file is empty
            # This verifies the `and not has_explicit_input` condition works
            mock_fetch.assert_not_called()
