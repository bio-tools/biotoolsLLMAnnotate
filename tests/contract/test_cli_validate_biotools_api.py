"""Test CLI bio.tools API validation feature."""

import json
import os
import subprocess
import sys
from pathlib import Path

import yaml


def test_validate_biotools_api_enabled_in_config(tmp_path):
    """Test that validate_biotools_api in config triggers API validation.

    Contract assumptions:
    - When validate_biotools_api is true in config, validation runs
    - Assessment report contains biotools_api_status field
    - Offline mode prevents actual API calls but preserves field names
    """
    # Create minimal input file
    input_file = tmp_path / "input.json"
    input_data = {
        "count": 1,
        "list": [
            {
                "name": "TestTool",
                "biotoolsID": "test_tool",
                "description": "A test bioinformatics tool for RNA-seq analysis",
                "homepage": "https://example.com/testtool",
                "function": [
                    {
                        "operation": [
                            {
                                "uri": "http://edamontology.org/operation_3680",
                                "term": "RNA-Seq analysis",
                            }
                        ]
                    }
                ],
                "topic": [
                    {
                        "uri": "http://edamontology.org/topic_3170",
                        "term": "RNA-Seq",
                    }
                ],
                "confidence_flag": "high",
            }
        ],
    }
    input_file.write_text(json.dumps(input_data))

    # Create config with validate_biotools_api enabled
    config_data = {
        "pipeline": {
            "custom_pub2tools_biotools_json": str(input_file),
            "validate_biotools_api": True,
            "bio_score_thresholds": {"add": 0.0, "review": 0.0},
            "documentation_score_thresholds": {"add": 0.0, "review": 0.0},
        },
        "enrichment": {
            "europe_pmc": {"enabled": False},
            "homepage": {"enabled": False},
        },
        "pub2tools": {},
    }

    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(config_data, sort_keys=False))

    # Setup environment
    env = os.environ.copy()
    repo_root = Path(__file__).resolve().parents[2]
    env["PYTHONPATH"] = str(repo_root / "src")

    # Run CLI
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "biotoolsllmannotate",
            "--config",
            str(config_path),
            "--offline",
        ],
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        cwd=str(tmp_path),
    )

    # Check command succeeded
    assert (
        proc.returncode == 0
    ), f"Command failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"

    # Check assessment report contains validation status
    assessment_file = (
        tmp_path / "out" / "custom_tool_set" / "reports" / "assessment.jsonl"
    )
    assert assessment_file.exists(), f"Assessment file not found: {assessment_file}"

    with open(assessment_file) as f:
        row = json.loads(f.readline())
        # Verify validation was run - biotools_api_status should be present
        assert (
            "biotools_api_status" in row
        ), f"biotools_api_status field should be present when validation is enabled. Keys: {list(row.keys())}"
        # In offline mode, API call will actually execute (offline only affects pub2tools)
        # With biotoolsID present, it should attempt validation
        assert row["biotools_api_status"] in [
            "ok",
            "not_found",
            "no_id",
            "error",
        ], f"Unexpected status: {row['biotools_api_status']}"


def test_validate_biotools_api_disabled_by_default(tmp_path):
    """Test that validation is not run when validate_biotools_api is not set.

    Contract assumptions:
    - Without validate_biotools_api in config, validation does not run
    - Assessment report generated normally without validation fields
    """
    # Create minimal input file
    input_file = tmp_path / "input.json"
    input_data = {
        "count": 1,
        "list": [
            {
                "name": "TestTool",
                "description": "A test bioinformatics tool",
                "homepage": "https://example.com/testtool",
                "function": [
                    {
                        "operation": [
                            {
                                "uri": "http://edamontology.org/operation_3680",
                                "term": "RNA-Seq analysis",
                            }
                        ]
                    }
                ],
                "topic": [
                    {
                        "uri": "http://edamontology.org/topic_3170",
                        "term": "RNA-Seq",
                    }
                ],
                "confidence_flag": "high",
            }
        ],
    }
    input_file.write_text(json.dumps(input_data))

    # Create config WITHOUT validate_biotools_api
    config_data = {
        "pipeline": {
            "custom_pub2tools_biotools_json": str(input_file),
            "bio_score_thresholds": {"add": 0.0, "review": 0.0},
            "documentation_score_thresholds": {"add": 0.0, "review": 0.0},
        },
        "enrichment": {
            "europe_pmc": {"enabled": False},
            "homepage": {"enabled": False},
        },
        "pub2tools": {},
    }

    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(config_data, sort_keys=False))

    # Setup environment
    env = os.environ.copy()
    repo_root = Path(__file__).resolve().parents[2]
    env["PYTHONPATH"] = str(repo_root / "src")

    # Run CLI
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "biotoolsllmannotate",
            "--config",
            str(config_path),
            "--offline",
        ],
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        cwd=str(tmp_path),
    )

    # Check command succeeded
    assert (
        proc.returncode == 0
    ), f"Command failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"

    # Check assessment report exists
    assessment_file = (
        tmp_path / "out" / "custom_tool_set" / "reports" / "assessment.jsonl"
    )
    assert assessment_file.exists(), f"Assessment file not found: {assessment_file}"

    with open(assessment_file) as f:
        row = json.loads(f.readline())
        # Verify validation was NOT run - biotools_api_status should be absent
        assert (
            "biotools_api_status" not in row
        ), f"biotools_api_status field should NOT be present when validation is disabled. Keys: {list(row.keys())}"


def test_validate_biotools_api_cli_flag_overrides_config(tmp_path):
    """Test that --validate-biotools-api CLI flag enables validation.

    Contract assumptions:
    - CLI flag --validate-biotools-api enables validation
    - Overrides config setting (if False or missing)
    - Assessment report contains validation status
    """
    # Create minimal input file
    input_file = tmp_path / "input.json"
    input_data = {
        "count": 1,
        "list": [
            {
                "name": "TestTool",
                "biotoolsID": "test_tool",
                "description": "A test bioinformatics tool",
                "homepage": "https://example.com/testtool",
                "function": [
                    {
                        "operation": [
                            {
                                "uri": "http://edamontology.org/operation_3680",
                                "term": "RNA-Seq analysis",
                            }
                        ]
                    }
                ],
                "topic": [
                    {
                        "uri": "http://edamontology.org/topic_3170",
                        "term": "RNA-Seq",
                    }
                ],
                "confidence_flag": "high",
            }
        ],
    }
    input_file.write_text(json.dumps(input_data))

    # Create config with validation disabled
    config_data = {
        "pipeline": {
            "custom_pub2tools_biotools_json": str(input_file),
            "validate_biotools_api": False,
            "bio_score_thresholds": {"add": 0.0, "review": 0.0},
            "documentation_score_thresholds": {"add": 0.0, "review": 0.0},
        },
        "enrichment": {
            "europe_pmc": {"enabled": False},
            "homepage": {"enabled": False},
        },
        "pub2tools": {},
    }

    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(config_data, sort_keys=False))

    # Setup environment
    env = os.environ.copy()
    repo_root = Path(__file__).resolve().parents[2]
    env["PYTHONPATH"] = str(repo_root / "src")

    # Run CLI with --validate-biotools-api flag
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "biotoolsllmannotate",
            "--config",
            str(config_path),
            "--validate-biotools-api",
            "--offline",
        ],
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        cwd=str(tmp_path),
    )

    # Check command succeeded
    assert (
        proc.returncode == 0
    ), f"Command failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"

    # Check assessment report contains validation status
    assessment_file = (
        tmp_path / "out" / "custom_tool_set" / "reports" / "assessment.jsonl"
    )
    assert assessment_file.exists(), f"Assessment file not found: {assessment_file}"

    with open(assessment_file) as f:
        row = json.loads(f.readline())
        # Verify CLI flag override worked - biotools_api_status should be present even though config had False
        assert (
            "biotools_api_status" in row
        ), f"biotools_api_status field should be present when CLI flag is used. Keys: {list(row.keys())}"
        # In offline mode, API call will actually execute (offline only affects pub2tools)
        # With biotoolsID present, it should attempt validation
        assert row["biotools_api_status"] in [
            "ok",
            "not_found",
            "no_id",
            "error",
        ], f"Unexpected status: {row['biotools_api_status']}"
