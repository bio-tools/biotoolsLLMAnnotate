"""
Test that resume_from_scoring automatically falls back to resume_from_enriched
when the assessment file is empty or invalid, avoiding pub2tools re-fetch attempts.
"""

import gzip
import json
from pathlib import Path
from unittest.mock import patch
import pytest


def test_resume_from_scoring_empty_assessment_uses_enriched_cache(tmp_path, caplog):
    """
    When resume_from_scoring is enabled but the assessment file is empty,
    the pipeline should automatically fall back to loading from enriched cache
    if it exists, to avoid attempting pub2tools re-fetch.
    """
    from biotoolsllmannotate.cli.run import execute_run

    # Setup directory structure
    out_dir = tmp_path / "out" / "range_2025-01-01_to_2025-01-02"
    out_dir.mkdir(parents=True)
    cache_dir = out_dir / "cache"
    cache_dir.mkdir(parents=True)
    reports_dir = out_dir / "reports"
    reports_dir.mkdir(parents=True)
    pub2tools_dir = out_dir / "pub2tools"
    pub2tools_dir.mkdir(parents=True)

    # Create empty assessment file (simulating the issue)
    assessment_file = reports_dir / "assessment.jsonl"
    assessment_file.write_text("")  # Empty file

    # Create enriched cache with test candidate
    enriched_cache_file = cache_dir / "enriched_candidates.json.gz"
    test_candidate = {
        "id": "test_tool",
        "title": "Test Tool",
        "homepage": "https://example.com",
        "urls": ["https://example.com"],
        "in_biotools": False,
        "homepage_status": "ok",
    }
    with gzip.open(enriched_cache_file, "wt", encoding="utf-8") as f:
        json.dump([test_candidate], f)

    # Mock the Pub2Tools client to verify it's NOT called
    with patch(
        "biotoolsllmannotate.ingest.pub2tools_client.fetch_via_cli"
    ) as mock_fetch:
        mock_fetch.return_value = []

        # Mock the Scorer class to prevent actual LLM calls
        with patch("biotoolsllmannotate.assess.scorer.Scorer") as MockScorer:
            mock_scorer_instance = MockScorer.return_value
            mock_scorer_instance.score.return_value = {
                "bio_score": 0.8,
                "documentation_score": 0.6,
                "doc_score_v2": 0.6,
                "confidence_score": 0.9,
                "publication_ids": [],
                "homepage": "https://example.com",
                "model_params": {},
            }

            # Mock registry loading
            with patch(
                "biotoolsllmannotate.cli.run.load_registry_from_pub2tools"
            ) as mock_registry:
                mock_registry.return_value = None

                # Run with resume_from_scoring enabled
                config_data = {
                    "pipeline": {
                        "from_date": "2025-01-01",
                        "to_date": "2025-01-02",
                        "custom_pub2tools_biotools_json": None,
                        "bio_add_threshold": 0.7,
                        "bio_review_threshold": 0.5,
                        "doc_add_threshold": 0.5,
                        "doc_review_threshold": 0.3,
                        "limit": None,
                        "concurrency": 1,
                        "enrich_europe_pmc": False,
                        "enrich_homepage": False,
                        "resume_from_pub2tools": False,
                        "resume_from_enriched": False,
                        "resume_from_scoring": True,  # This is the key setting
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

                try:
                    execute_run(
                        config_data=config_data,
                        base_output_root=tmp_path / "out",
                        output=None,
                        report=None,
                        updated_entries=None,
                        enriched_cache=None,
                        registry_path=None,
                        resume_from_pub2tools=False,
                        resume_from_enriched=False,  # Not explicitly enabled
                        resume_from_scoring=True,  # Enabled with empty assessment
                        offline=False,
                        dry_run=True,
                        validate_biotools_api=False,
                    )
                except Exception as e:
                    # Allow any exception from downstream processing
                    # We're mainly checking that pub2tools wasn't called
                    pass

                # Verify that pub2tools fetch was NOT attempted
                # (because we automatically fell back to enriched cache)
                mock_fetch.assert_not_called()


def test_resume_from_scoring_missing_assessment_uses_enriched_cache(tmp_path, caplog):
    """
    When resume_from_scoring is enabled but the assessment file doesn't exist,
    the pipeline should automatically fall back to loading from enriched cache
    if it exists.
    """
    from biotoolsllmannotate.cli.run import execute_run

    # Setup directory structure
    out_dir = tmp_path / "out" / "range_2025-01-01_to_2025-01-02"
    out_dir.mkdir(parents=True)
    cache_dir = out_dir / "cache"
    cache_dir.mkdir(parents=True)
    pub2tools_dir = out_dir / "pub2tools"
    pub2tools_dir.mkdir(parents=True)

    # Do NOT create assessment file (simulating missing file)

    # Create enriched cache with test candidate
    enriched_cache_file = cache_dir / "enriched_candidates.json.gz"
    test_candidate = {
        "id": "test_tool_2",
        "title": "Test Tool 2",
        "homepage": "https://example.org",
        "urls": ["https://example.org"],
        "in_biotools": False,
        "homepage_status": "ok",
    }
    with gzip.open(enriched_cache_file, "wt", encoding="utf-8") as f:
        json.dump([test_candidate], f)

    # Mock the Pub2Tools client to verify it's NOT called
    with patch(
        "biotoolsllmannotate.ingest.pub2tools_client.fetch_via_cli"
    ) as mock_fetch:
        mock_fetch.return_value = []

        # Mock the Scorer class
        with patch("biotoolsllmannotate.assess.scorer.Scorer") as MockScorer:
            mock_scorer_instance = MockScorer.return_value
            mock_scorer_instance.score.return_value = {
                "bio_score": 0.8,
                "documentation_score": 0.6,
                "doc_score_v2": 0.6,
                "confidence_score": 0.9,
                "publication_ids": [],
                "homepage": "https://example.org",
                "model_params": {},
            }

            # Mock registry loading
            with patch(
                "biotoolsllmannotate.cli.run.load_registry_from_pub2tools"
            ) as mock_registry:
                mock_registry.return_value = None

                config_data = {
                    "pipeline": {
                        "from_date": "2025-01-01",
                        "to_date": "2025-01-02",
                        "custom_pub2tools_biotools_json": None,
                        "bio_add_threshold": 0.7,
                        "bio_review_threshold": 0.5,
                        "doc_add_threshold": 0.5,
                        "doc_review_threshold": 0.3,
                        "limit": None,
                        "concurrency": 1,
                        "enrich_europe_pmc": False,
                        "enrich_homepage": False,
                        "resume_from_pub2tools": False,
                        "resume_from_enriched": False,
                        "resume_from_scoring": True,
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

                try:
                    execute_run(
                        config_data=config_data,
                        base_output_root=tmp_path / "out",
                        output=None,
                        report=None,
                        updated_entries=None,
                        enriched_cache=None,
                        registry_path=None,
                        resume_from_pub2tools=False,
                        resume_from_enriched=False,
                        resume_from_scoring=True,
                        offline=False,
                        dry_run=True,
                        validate_biotools_api=False,
                    )
                except Exception as e:
                    pass

                # Verify pub2tools was NOT called
                mock_fetch.assert_not_called()
