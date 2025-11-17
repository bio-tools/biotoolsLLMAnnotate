# Spec Delta: CLI Pipeline - Pub2Tools Folder Management

## ADDED Requirements

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

## MODIFIED Requirements

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
