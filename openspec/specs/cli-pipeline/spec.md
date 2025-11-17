# Capability: CLI Pipeline

## Purpose
Document the existing end-to-end CLI pipeline so future changes can reference the baseline gather→dedup→enrich→score→output workflow, its gating logic, and the produced artifacts.
## Requirements
### Requirement: Pipeline Stage Progression
The CLI pipeline SHALL execute the gather, deduplicate, enrich, score, and output stages sequentially for every run and SHALL emit status updates for each stage via the logger and progress renderer.

#### Scenario: Standard run updates every stage
- **WHEN** `execute_run` starts without early exits
- **THEN** the logger reports "GATHER", "DEDUP", "ENRICH", "SCORE", and "OUTPUT" stages in order
- **AND** the status renderer tracks progress for each stage until completion

### Requirement: Candidate Ingestion Order
The pipeline SHALL source candidates in the following priority: (1) resume from an enriched cache when requested and available, (2) reuse Pub2Tools exports from the canonical `out/pub2tools/range_<from>_to_<to>/` folder OR explicit custom input files, and (3) invoke the Pub2Tools CLI when no local input is available and the run is not offline.

**Changes from original**:
- Added reference to canonical Pub2Tools folder (`out/pub2tools/range_<from>_to_<to>/`)
- Clarified that resume search includes both pipeline-specific cache (`out/range_*/pub2tools/`) and global Pub2Tools cache

#### Scenario: Custom input file is loaded (unchanged)
- **WHEN** `pipeline.custom_pub2tools_biotools_json` is set to a valid file path
- **THEN** the pipeline loads candidates from that file and uses `custom_tool_set` as the output directory label

#### Scenario: Date-based query uses date-based folder (unchanged)
- **WHEN** `pipeline.custom_pub2tools_biotools_json` is null and date parameters are provided
- **THEN** the pipeline uses `out/range_YYYY-MM-DD_to_YYYY-MM-DD/` as the output directory label regardless of resume flags

#### Scenario: Resume finds canonical Pub2Tools cache (new)
- **GIVEN** `out/pub2tools/range_2025-01-01_to_2025-01-15/to_biotools.json` exists
- **AND** `out/range_2025-01-01_to_2025-01-15/pub2tools/to_biotools.json` does NOT exist
- **WHEN** the pipeline runs with `--resume-from-pub2tools` and matching date range
- **THEN** the pipeline searches `out/pub2tools/range_2025-01-01_to_2025-01-15/` as a fallback location
- **AND** successfully loads candidates without invoking the Pub2Tools CLI

#### Scenario: Offline run skips Pub2Tools fetch (unchanged)
- **WHEN** no local input exists and `offline=True`
- **THEN** the pipeline SHALL NOT call the Pub2Tools CLI and proceeds with an empty candidate list

### Requirement: Enrichment Controls
The pipeline SHALL scrape homepages and enrich Europe PMC metadata only when the respective enrichment flags are enabled, the run is online, and the execution is not resuming from an enriched cache; otherwise, it SHALL log that the enrichment step was skipped with the reason.

#### Scenario: Online enrichment executes
- **WHEN** enrichment is enabled, `offline=False`, and no enriched cache is reused
- **THEN** the pipeline invokes homepage scraping for each candidate and Europe PMC enrichment with progress updates

#### Scenario: Offline run documents skipped enrichment
- **WHEN** `offline=True`
- **THEN** both homepage scraping and Europe PMC enrichment are skipped and the logger notes the offline reason

### Requirement: Scoring and Classification Rules
The pipeline SHALL use LLM scoring by default, fall back to heuristic scoring when the run is offline or the LLM health check fails, compute `doc_score_v2` using weighted documentation subscores, and only classify a candidate as `add` when both bio and documentation thresholds are met **and** the execution path (B2 ≥ 0.5 or A4 = 1.0) and reproducibility anchor (B3 ≥ 0.5) gates pass; otherwise the candidate SHALL be classified as `review` or `do_not_add`.

#### Scenario: LLM scoring with gating passes
- **WHEN** the LLM is healthy and documentation subscores satisfy B2 ≥ 0.5 and B3 ≥ 0.5 while scores meet add thresholds
- **THEN** the candidate is classified as `add`

#### Scenario: Gating failure downgrades decision
- **WHEN** the documentation score meets thresholds but B3 = 0
- **THEN** the candidate is classified as `review` despite high aggregate scores

#### Scenario: Offline scoring uses heuristics
- **WHEN** `offline=True`
- **THEN** heuristic scoring executes for every candidate and the logger records the heuristic mode

### Requirement: Output Artifacts
Upon finishing scoring, the pipeline SHALL write the assessment report as JSONL and CSV, produce add and review payload JSON files (unless `dry_run=True`), update the entries snapshot, and terminate with an error when payload validation fails; payloads SHALL omit nested null fields.

#### Scenario: Successful output writes artifacts
- **WHEN** the run completes without validation errors and `dry_run=False`
- **THEN** the pipeline writes `<report>.jsonl`, `<report>.csv`, `biotools_payload.json`, `biotools_review_payload.json`, and `biotools_entries.json`

#### Scenario: Validation errors raise failure
- **WHEN** a payload entry fails schema validation
- **THEN** the pipeline writes an `.invalid.json` report and exits with a non-zero status

### Requirement: Homepage Metadata Extraction
The enrichment stage SHALL fetch homepage content with configurable timeouts, byte-size guardrails, and iframe limits, reject publication-only URLs, and merge documentation, repository, and keyword metadata from both the root document and a bounded crawl of nested frames; it SHALL emit homepage status and error labels when fetching fails. Before recording any anchor as a documentation link, the scraper SHALL exclude generic repository navigation paths (issues, pulls, releases, tags, commits, branches, contributors, stargazers, watchers, forks, milestones, labels, and platform-specific variants) and platform global navigation links (features, about, blog, changelog, pricing, support, docs subdomains) that do not provide tool-specific information.

#### Scenario: Publication homepage is filtered
- **WHEN** the primary homepage candidate resolves to a publication URL and an alternative non-publication URL exists
- **THEN** the enrichment stage selects the non-publication URL and updates the candidate homepage accordingly

#### Scenario: Non-HTML content is reported
- **WHEN** the fetched homepage advertises a non-text content type or exceeds the byte limit
- **THEN** the enrichment stage marks `homepage_scraped=False`, records a descriptive `homepage_error`, and keeps the candidate available for scoring

#### Scenario: Frame crawl extends metadata
- **WHEN** nested frames yield additional documentation links or repository URLs before the frame fetch and depth limits are exhausted
- **THEN** the enrichment stage merges the new metadata into the candidate without duplicating existing documentation entries

#### Scenario: Generic repo navigation is excluded
- **WHEN** a repository homepage anchor points to /releases, /tags, /commits, /issues, /pulls, or any path matching generic navigation patterns
- **THEN** the scraper does NOT add that link to `candidate["documentation"]` regardless of keyword matches

#### Scenario: Platform global navigation is excluded
- **WHEN** an anchor resolves to a platform-wide support/docs/blog/features subdomain or path (e.g., docs.github.com, /features, /about, /pricing)
- **THEN** the scraper does NOT add that link to `candidate["documentation"]` even if it matches documentation keywords

#### Scenario: Layout ancestor filtering still applies
- **WHEN** an anchor sits within a detected layout container (nav, header, footer, sidebar) and has no matching documentation keywords
- **THEN** the scraper skips that anchor to avoid capturing site chrome unrelated to tool docs

### Requirement: LLM Scoring Output Normalisation
The scoring stage SHALL construct prompts from available candidate metadata, request JSON responses that satisfy the published schema, retry with schema error context, and normalise the payload into `bio_score`, `documentation_score`, `doc_score_v2`, publication IDs, homepage, and confidence values with bounded attempts tracking.

#### Scenario: Schema retries capture validation errors
- **WHEN** the initial LLM response is missing required fields
- **THEN** the scorer augments the prompt with validation errors, retries up to the configured limit, and raises a failure if the response never satisfies the schema

#### Scenario: Subscores are normalised and weighted
- **WHEN** the LLM returns numeric documentation subscores in any iterable or mapping form
- **THEN** the scorer normalises them into canonical B1–B5 keys, applies the weighted `doc_score_v2`, and exposes both the weighted score and raw breakdown in the result

#### Scenario: Publication IDs and homepage are sanitised
- **WHEN** publication identifiers or homepages are returned in string or list form
- **THEN** the scorer coerces them into trimmed lists, filters out publication-only homepages, and falls back to candidate URLs when the response omits a valid homepage

#### Scenario: Retry diagnostics are emitted
- **WHEN** schema retries occur or prompt augmentation is needed
- **THEN** the scorer records `model_params` telemetry containing the attempt count and per-attempt schema error details for downstream auditing

### Requirement: LLM Structured Telemetry
The pipeline scoring stage SHALL append a structured JSON line to the `logging.llm_trace` path for every Ollama `generate` attempt, defaulting to `<time_period>/ollama/trace.jsonl` when unspecified. Each record SHALL contain a unique `trace_id`, ISO-8601 UTC `timestamp`, `attempt` index, `prompt_kind` (`base` or `augmented`), the exact `prompt` text sent to Ollama, the serialized request options (`model`, `temperature`, `top_p`, `format`, `seed`), the raw concatenated `response_text`, the parsed `response_json` when available, and a `status` flag indicating `success`, `parse_error`, or `schema_error`.

The retry diagnostics exposed via `model_params` SHALL include a `trace_attempts` array mirroring the attempt order, where each element records the corresponding `trace_id`, `prompt_kind`, and any `schema_errors` captured during validation so downstream tools can join decisions with the trace log.

#### Scenario: Successful attempt recorded
- **WHEN** the first scoring attempt produces schema-valid JSON
- **THEN** the trace file gains an entry with `attempt=1`, `prompt_kind="base"`, `status="success"`, and a populated `response_json`
- **AND** `model_params.trace_attempts[0].trace_id` matches the appended entry

#### Scenario: Augmented retry captures schema failure
- **WHEN** the initial attempt fails schema validation and the scorer retries with an augmented prompt
- **THEN** the trace records the failed attempt with `status="schema_error"` alongside its validation messages and the retried attempt with `status="success"`
- **AND** `model_params.trace_attempts` lists both attempts with their trace identifiers and `prompt_kind` values

### Requirement: Output Directory Naming Logic
The pipeline SHALL use `custom_tool_set` as the output directory label ONLY when `pipeline.custom_pub2tools_biotools_json` (or environment variables `BIOTOOLS_ANNOTATE_INPUT` or `BIOTOOLS_ANNOTATE_JSON`) is explicitly set to a non-null value; otherwise it SHALL derive the directory name from the date range parameters as `range_<from_date>_to_<to_date>`. The presence of existing `custom_tool_set` directories or resume flags SHALL NOT influence this decision.

#### Scenario: Custom input triggers custom directory
- **WHEN** `pipeline.custom_pub2tools_biotools_json: "path/to/to_biotools.json"` is set
- **THEN** the pipeline uses `out/custom_tool_set/` for all output artifacts

#### Scenario: Null parameter with resume uses date-based directory
- **WHEN** `pipeline.custom_pub2tools_biotools_json: null` and `resume_from_enriched: true` and `from_date: "2025-01-01"` and `to_date: "2025-01-15"`
- **THEN** the pipeline uses `out/range_2025-01-01_to_2025-01-15/` for output artifacts

#### Scenario: Existing custom_tool_set directory is ignored
- **WHEN** `out/custom_tool_set/` exists from a previous run AND `pipeline.custom_pub2tools_biotools_json: null` AND date parameters are provided
- **THEN** the pipeline uses `out/range_YYYY-MM-DD_to_YYYY-MM-DD/` and does NOT reuse the existing custom_tool_set directory

#### Scenario: Environment variable overrides null config
- **WHEN** `pipeline.custom_pub2tools_biotools_json: null` AND `BIOTOOLS_ANNOTATE_INPUT` environment variable is set to a file path
- **THEN** the pipeline uses `out/custom_tool_set/` as if the config parameter was set

### Requirement: Configuration Parameter Naming
The pipeline configuration SHALL accept `pipeline.custom_pub2tools_biotools_json` as the parameter name for specifying a custom Pub2Tools JSON export file. The CLI SHALL accept `--custom-pub2tools-json` as the corresponding command-line flag. The legacy `pipeline.input_path` and `--input` names SHALL be deprecated.

#### Scenario: New parameter name is recognized
- **WHEN** config contains `pipeline.custom_pub2tools_biotools_json: "file.json"`
- **THEN** the pipeline loads candidates from the specified file

#### Scenario: CLI flag is recognized
- **WHEN** user runs `python -m biotoolsllmannotate run --custom-pub2tools-json file.json`
- **THEN** the CLI passes the file path to the pipeline execution

#### Scenario: Legacy parameter shows deprecation warning
- **WHEN** config contains `pipeline.input_path: "file.json"` instead of the new parameter name
- **THEN** the system logs a deprecation warning suggesting migration to `pipeline.custom_pub2tools_biotools_json`

### Requirement: Canonical Pub2Tools Output Folders
The Pub2Tools CLI wrapper SHALL write outputs to a canonical folder named `out/pub2tools/range_<from_date>_to_<to_date>` derived solely from the date range parameters, WITHOUT appending timestamp suffixes, and SHALL reuse this folder for all invocations with identical date ranges; existing outputs SHALL be overwritten on subsequent runs.

#### Scenario: First run creates canonical folder
- **GIVEN** no existing Pub2Tools output for the date range `2025-01-01` to `2025-01-15`
- **WHEN** `fetch_candidates_all` is invoked with `since="2025-01-01"` and `to_date="2025-01-15"`
- **THEN** the wrapper creates `out/pub2tools/range_2025-01-01_to_2025-01-15/`
- **AND** the Pub2Tools CLI writes `to_biotools.json` and intermediate files to that folder
- **AND** no timestamp suffix appears in the folder name

#### Scenario: Second run reuses canonical folder
- **GIVEN** existing folder `out/pub2tools/range_2025-01-01_to_2025-01-15/` with `to_biotools.json` from a previous run
- **WHEN** `fetch_candidates_all` is invoked again with the same date range
- **THEN** the wrapper reuses `out/pub2tools/range_2025-01-01_to_2025-01-15/`
- **AND** deletes the existing `to_biotools.json` before invoking the Pub2Tools CLI
- **AND** the Pub2Tools CLI overwrites all output files in the folder
- **AND** the folder modification timestamp reflects the second run

#### Scenario: Different date ranges create different folders
- **GIVEN** existing folder `out/pub2tools/range_2025-01-01_to_2025-01-15/`
- **WHEN** `fetch_candidates_all` is invoked with `since="2025-02-01"` and `to_date="2025-02-15"`
- **THEN** the wrapper creates a new folder `out/pub2tools/range_2025-02-01_to_2025-02-15/`
- **AND** the existing folder remains untouched

#### Scenario: Resume from cached Pub2Tools output
- **GIVEN** existing folder `out/pub2tools/range_2025-01-01_to_2025-01-15/to_biotools.json`
- **AND** no cached export in the main pipeline folder `out/range_2025-01-01_to_2025-01-15/pub2tools/`
- **WHEN** the pipeline executes with `--resume-from-pub2tools` and the same date range
- **THEN** the resume search paths include `out/pub2tools/range_2025-01-01_to_2025-01-15/`
- **AND** the pipeline successfully loads candidates from the cached `to_biotools.json`
- **AND** no new Pub2Tools CLI invocation occurs

#### Scenario: Legacy timestamped folders are ignored
- **GIVEN** existing timestamped folders from old runs (e.g., `out/pub2tools/range_2025-01-01_to_2025-01-15_20251111T162353Z/`)
- **WHEN** `fetch_candidates_all` is invoked with `since="2025-01-01"` and `to_date="2025-01-15"`
- **THEN** the wrapper creates or reuses the canonical folder `out/pub2tools/range_2025-01-01_to_2025-01-15/`
- **AND** the legacy timestamped folders are left untouched for manual cleanup

### Requirement: Live bio.tools API Validation
The pipeline SHALL support an optional step, after scoring and registry membership checks, to validate each payload entry against the live bio.tools API or development server. The validation endpoint SHALL be configurable via the `biotools_validate_api_base` configuration field (defaulting to `https://bio.tools/api/tool/validate/`). When a `.bt_token` file exists in the repository root, the pipeline SHALL read the token and include an `Authorization: Token {token}` header in validation requests to support authenticated dev server access. The pipeline SHALL fall back to local Pydantic validation when the token file is missing, authentication fails (401/403), or the API is unreachable.

#### Scenario: Payload entry validated against dev server with token
- **GIVEN** a `.bt_token` file exists in the repository root
- **AND** `biotools_validate_api_base` is set to `https://bio-tools-dev.sdu.dk/api/tool/validate/`
- **WHEN** validation is enabled and the pipeline validates an entry
- **THEN** the validation request includes an `Authorization: Token {token}` header
- **AND** the dev server returns validation results
- **AND** the pipeline logs successful API validation

#### Scenario: Payload entry validated against production API with token
- **GIVEN** a `.bt_token` file exists in the repository root
- **AND** `biotools_validate_api_base` is set to `https://bio.tools/api/tool/validate/` (default)
- **WHEN** validation is enabled and the pipeline validates an entry
- **THEN** the validation request includes an `Authorization: Token {token}` header
- **AND** the pipeline logs validation results

#### Scenario: Token file missing falls back to local validation
- **GIVEN** no `.bt_token` file exists
- **WHEN** validation is enabled and `use_api=True`
- **THEN** the pipeline logs that token is missing
- **AND** falls back to local Pydantic validation
- **AND** all entries are validated against the local schema

#### Scenario: Authentication failure falls back to local validation
- **GIVEN** a `.bt_token` file exists but contains an invalid token
- **WHEN** validation is enabled and the API returns 401 or 403
- **THEN** the pipeline logs the authentication error
- **AND** automatically falls back to local Pydantic validation
- **AND** the entry is validated successfully using the local schema

#### Scenario: Payload entry matches live bio.tools record
- **GIVEN** a payload entry with a valid bio.tools ID
- **WHEN** live validation is enabled
- **AND** the pipeline queries the bio.tools API for that ID
- **THEN** the API returns a matching record
- **AND** the pipeline logs successful validation

#### Scenario: Payload entry missing in live bio.tools
- **GIVEN** a payload entry with a bio.tools ID not present in the live registry
- **WHEN** live validation is enabled
- **AND** the pipeline queries the bio.tools API for that ID
- **THEN** the API returns a 404 or error
- **AND** the pipeline logs a warning and flags the entry for review

#### Scenario: API validation disabled
- **GIVEN** the validation feature is disabled by config or CLI flag
- **WHEN** the pipeline runs
- **THEN** no live API queries are made
- **AND** the pipeline proceeds as before

#### Scenario: API/network error
- **GIVEN** a network or API error occurs during validation
- **WHEN** the pipeline queries the API
- **THEN** the error is logged
- **AND** the pipeline continues processing other entries

