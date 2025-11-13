# Spec Delta: Custom Input Clarification

## MODIFIED Requirements

### Requirement: Candidate Ingestion Order
The pipeline SHALL source candidates in the following priority: (1) resume from an enriched cache when requested and available, (2) reuse Pub2Tools exports or explicit custom input files, and (3) invoke the Pub2Tools CLI when no local input is available and the run is not offline.

#### Scenario: Resume from enriched cache succeeds
- **WHEN** `--resume-from-enriched` is set and the cache file exists
- **THEN** the pipeline reloads candidates from the cache and skips fetching from other sources

#### Scenario: Custom input file is loaded
- **WHEN** `pipeline.custom_pub2tools_biotools_json` is set to a valid file path
- **THEN** the pipeline loads candidates from that file and uses `custom_tool_set` as the output directory label

#### Scenario: Date-based query uses date-based folder
- **WHEN** `pipeline.custom_pub2tools_biotools_json` is null and date parameters are provided
- **THEN** the pipeline uses `out/range_YYYY-MM-DD_to_YYYY-MM-DD/` as the output directory label regardless of resume flags

#### Scenario: Offline run skips Pub2Tools fetch
- **WHEN** no local input exists and `offline=True`
- **THEN** the pipeline SHALL NOT call the Pub2Tools CLI and proceeds with an empty candidate list

## ADDED Requirements

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

## REMOVED Requirements

None. This change enhances existing requirements without removing functionality.
