# BioToolsLLMAnnotate

CLI tools for discovering, enriching, and annotating bio.tools entries with help from Pub2Tools, heuristic scraping, and Ollama-based scoring.

## Table of Contents
- [Overview](#overview)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
  - [Core settings](#core-settings)
- [Running the Pipeline](#running-the-pipeline)
- [Generated Outputs](#generated-outputs)
- [Resume & Caching](#resume--caching)
- [Troubleshooting & Tips](#troubleshooting--tips)
- [Development](#development)
- [License](#license)
- [Documentation](#documentation)

## Overview
- Fetch candidate records from Pub2Tools exports or existing JSON files.
- Enrich candidates with homepage metadata, documentation links, repositories, and publication context.
- Score bioinformatics relevance and documentation quality using an Ollama model.
- Generate optimized, concise descriptions through LLM scoring while preserving EDAM annotations.
- Produce strict biotoolsSchema payloads plus human-readable assessment reports.
- Resume any stage (gather, enrich, score) using cached artifacts to accelerate iteration.

## Documentation
- [Architecture and Data Flow](docs/architecture.md)
- [Configuration Manual](CONFIG.md)

## Installation
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
ollama pull llama3.2  # optional, only needed for LLM scoring
```

> Need defaults? Generate a starter configuration with:
> ```bash
> biotoolsannotate --write-default-config
> ```

## Quick Start
```bash
# Dry-run against sample data (no network calls)
biotoolsannotate --input tests/fixtures/pub2tools/sample.json --dry-run

# Fetch fresh candidates from the last 7 days and score them
biotoolsannotate --from-date 7d --min-score 0.6

# Re-run only the scoring step with cached enrichment
biotoolsannotate --resume-from-enriched --resume-from-scoring --dry-run
```

## Configuration
Configuration is YAML-driven. The CLI loads `config.yaml` from the project root by default and falls back to internal defaults when absent. All placeholders marked `__VERSION__` resolve to the installed package version at runtime. 

During each run the pipeline scans the Pub2Tools export folders (for example `pub2tools/to_biotools.json` or `pub2tools/biotools_entries.json`) and uses them to flag candidates already present in bio.tools. When the Pub2Tools CLI is invoked, outputs are written directly to `out/range_<from>_to_<to>/pub2tools/`. You can also point to any standalone registry snapshot via `pipeline.registry_path` or `--registry` when you want to bypass Pub2Tools exports entirely.

### Core settings
| Purpose | Config key | CLI flag | Notes |
| --- | --- | --- | --- |
| Custom input | `pipeline.custom_pub2tools_biotools_json` | `--custom-pub2tools-json PATH` | Use a custom Pub2Tools to_biotools.json export instead of date-based fetching |
| Registry snapshot | `pipeline.registry_path` | `--registry PATH` | Supply an external bio.tools JSON/JSONL snapshot for membership checks |
| Date range | `pipeline.from_date`, `pipeline.to_date` | `--from-date`, `--to-date` | Accepts relative windows like `7d` or ISO dates |
| Thresholds | `pipeline.min_bio_score`, `pipeline.min_documentation_score` | `--min-bio-score`, `--min-doc-score` | Set both via legacy `--min-score` if desired |
| bio.tools API validation | `pipeline.validate_biotools_api` | `--validate-biotools-api` | Validate payload entries against live bio.tools API after scoring (default: `false`). See [bio.tools API Validation Setup](#biotools-api-validation-setup) below. |
| Upload to bio.tools | `pipeline.upload.enabled` | `--upload` | Upload new entries to bio.tools registry after payload generation (requires `.bt_token` file). See [Uploading to bio.tools](#uploading-to-biotools) below. |
| Offline mode | `pipeline.offline` | `--offline` | Disables homepage scraping and Europe PMC enrichment |
| Ollama model | `ollama.model` | `--model` | Defaults to `llama3.2`; override per run |
| LLM temperature | `ollama.temperature` | (config only) | Lower values tighten determinism; default is `0.01` for high-precision scoring |
| Concurrency | `ollama.concurrency` | `--concurrency` | Controls parallel scoring workers |
| Logging | `logging.level`, `logging.file` | `--verbose`, `--quiet` | Flags override log level; file path set in config |

## Running the Pipeline
Common invocations:
```bash
# Custom date window
biotoolsannotate --from-date 2024-01-01 --to-date 2024-03-31

# Offline mode (no network scraping or Europe PMC requests)
biotoolsannotate --offline

# Start from local candidates and separate registry snapshot
biotoolsannotate --input data/candidates.json --registry data/biotools_snapshot.json --offline

# Limit the number of candidates processed
biotoolsannotate --limit 25

# Point to a specific config file
biotoolsannotate --config myconfig.yaml
```

Use `biotoolsannotate --help` to explore all available flags, including concurrency settings, progress display, and resume options.

## bio.tools API Validation Setup

To enable live validation of generated payloads against the bio.tools schema:

1. **Obtain a token** from the bio.tools team for the development server.
2. **Create `.bt_token` file** in the repository root:
   ```bash
   echo "your-dev-token" > .bt_token
   ```
3. **Configure dev endpoints** in your config file (e.g., `myconfig.yaml`):
   ```yaml
   pipeline:
     validate_biotools_api: true
     biotools_api_base: "https://bio-tools-dev.sdu.dk/api/tool/"
     biotools_validate_api_base: "https://bio-tools-dev.sdu.dk/api/tool/validate/"
   ```
4. **Run the pipeline**:
   ```bash
   biotoolsannotate --config myconfig.yaml
   ```

Look for `✓ Found bio.tools authentication token` in the console output. If no token is present, the pipeline falls back to local Pydantic validation automatically.

For detailed setup, troubleshooting, and current limitations, see [`docs/BIOTOOLS_API_VALIDATION.md`](docs/BIOTOOLS_API_VALIDATION.md).

## Uploading to bio.tools

After generating and validating payloads, you can upload new entries directly to the bio.tools registry:

1. **Obtain a token** from the bio.tools team (development or production).
2. **Create `.bt_token` file** in the repository root:
   ```bash
   echo "your-token-here" > .bt_token
   ```
3. **Run the pipeline with upload enabled**:
   ```bash
   biotoolsannotate --upload
   ```

The pipeline will:
- Check each entry against the bio.tools registry (via GET request)
- Upload new entries using POST (returns `201 Created`)
- Skip entries that already exist with status `"skipped"`
- Retry transient server errors (503, 504) with exponential backoff
- Log all outcomes to `upload_results.jsonl`

**Note**: The upload feature only creates new entries. Existing tools will NOT be updated—they are skipped with a status message.

### Upload Configuration

Control upload behavior in your `config.yaml`:

```yaml
pipeline:
  upload:
    enabled: false          # Set true to enable by default
    retry_attempts: 3       # Number of retries for transient errors
    retry_delay: 1.0        # Initial delay in seconds (exponential backoff)
    batch_delay: 0.5        # Delay between entries to avoid rate limits
    log_file: "upload_results.jsonl"  # Result tracking file
```

Upload results include:
- `biotools_id`: Tool identifier
- `status`: "uploaded", "failed", or "skipped"
- `error`: Error message if failed
- `response_code`: HTTP status code
- `timestamp`: Upload attempt timestamp

## Generated Outputs
Each run writes artifacts to one of the following folders:

- `out/<range_start>_to_<range_end>/...` when the pipeline gathers candidates from Pub2Tools.
- `out/custom_tool_set/...` whenever you supply `--input` or set `BIOTOOLS_ANNOTATE_INPUT/JSON` (resume flags reuse the same directory).

The selected folder contains:

| Path | Description |
| --- | --- |
| `exports/biotools_payload.json` | biotoolsSchema-compliant payload ready for upload |
| `exports/biotools_entries.json` | Full entries including enriched metadata |
| `reports/assessment.csv` | **Primary assessment file** - spreadsheet-friendly scoring results (includes `in_biotools`, `confidence_score`, and **`manual_decision`** for overriding decisions; adds `biotools_api_status`, `api_name`, and `api_description` when `--validate-biotools-api` is enabled) |
| `cache/enriched_candidates.json.gz` | Cached candidates after enrichment for quick resumes |
| `logs/ollama/ollama.log` | Human-readable append-only log of every LLM request and response |
| `ollama/trace.jsonl` | Machine-readable trace with prompt variants, options, statuses, and parsed JSON payloads |
| `config.generated.yaml` or `<original-config>.yaml` | Snapshot of the configuration used for the run |

### LLM telemetry

Each record in `reports/assessment.jsonl` carries a `model_params` object describing how the LLM behaved during scoring. Key fields include:

| Field | Meaning |
| --- | --- |
| `attempts` | Number of prompt/response cycles the scorer performed (minimum 1) |
| `schema_errors` | Ordered list of validation errors returned by the JSON schema validator for each failed attempt |
| `prompt_augmented` | `true` when the scorer appended schema error feedback to the prompt before retrying |
| `trace_attempts` | Ordered list of trace metadata objects (`trace_id`, `attempt`, `prompt_kind`, `status`, `schema_errors`) that aligns with the JSONL trace for reproducible auditing |

These diagnostics mirror the telemetry requirement captured in OpenSpec and help correlate downstream decisions with LLM stability. Consumers that previously ignored `model_params` should update their parsers to accommodate the new keys.

### Confidence calibration

The LLM now follows an explicit rubric when emitting the `confidence_score` field. Expect values near 0.9–1.0 only when every subcriterion is backed by clear evidence from multiple sources; mixed or inferred evidence should land around 0.3–0.8, and scarce/conflicting evidence should drop to 0.0–0.2. Review the prompt template (either in `config.yaml` or your custom config) for the full guidance and adjust it further if your use case calls for a different calibration.

## Resume & Caching
- `--resume-from-pub2tools`: Reuse the latest `to_biotools.json` export for the active time range.
- `--resume-from-enriched`: Skip ingestion and reuse `cache/enriched_candidates.json.gz`.
- `--resume-from-scoring`: Reapply thresholds to assessment from `assessment.csv` without invoking the LLM. **Supports manual editing** of scores and decisions.

Combine the flags to iterate quickly on scoring thresholds and payload exports without repeating expensive steps.

### Manual Decision Overrides

The `assessment.csv` file now includes a **`manual_decision`** column (first column) that allows you to override the automatic classification:

| manual_decision | Effect |
| --- | --- |
| `add` | Force tool into "add" payload regardless of scores |
| `review` | Force tool into "review" payload |
| `do_not_add` | Exclude tool from all payloads |
| *(empty)* | Use automatic classification based on scores and thresholds |

When using `--resume-from-scoring`, you can also edit:
- **Scores**: `bio_score`, `documentation_score`, and subscores (`bio_A1`-`A5`, `doc_B1`-`B5`)
- **Registry flags**: `in_biotools_name`, `in_biotools`
- **Other metadata**: `homepage`, `publication_ids`, `rationale`, etc.

The pipeline will read your changes from the CSV and:
1. Use `manual_decision` if provided (overrides everything)
2. Otherwise re-classify based on edited scores and current thresholds

This enables human-in-the-loop refinement without re-running the expensive LLM scoring step.

## Troubleshooting & Tips
- Use `--offline` when working without network access; the pipeline disables homepage scraping and publication enrichment automatically.
- To inspect what the model saw, open `reports/assessment.csv` in any spreadsheet program.
- Use the `manual_decision` column in the CSV to override decisions when resuming from scoring.
- Health checks against the Ollama host run before scoring. Failures fall back to heuristics and are summarized in the run footer.
- Adjust logging verbosity with `--quiet` or `--verbose` as needed.

## Development
- Lint: `ruff check .`
- Format: `black .`
- Type check: `mypy src`
- Tests: `pytest -q`
- Coverage: `pytest --cov=biotoolsllmannotate --cov-report=term-missing`

## License
MIT
