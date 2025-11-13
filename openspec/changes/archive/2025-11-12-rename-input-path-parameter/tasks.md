# Tasks: Rename input-path Parameter

## Implementation Tasks

### 1. Update configuration schema and defaults
- [x] Rename `input_path` to `custom_pub2tools_biotools_json` in `src/biotoolsllmannotate/config.py`
- [x] Update default configuration dictionary
- [x] Add deprecation warning for old parameter name (if present)
- [x] Update documentation of parameter in config schema comments and CONFIG.md

### 2. Update CLI interface
- [x] Rename `input_path` parameter to `custom_pub2tools_biotools_json` in `src/biotoolsllmannotate/cli/main.py`
- [x] Update CLI option name from `--input` to `--custom-pub2tools-json`
- [x] Update validation logic that checks for conflicts with `--resume-from-pub2tools`
- [x] Update parameter passing to `execute_run()`

### 3. Fix custom_tool_set directory logic
- [x] Modify logic in `src/biotoolsllmannotate/cli/run.py` where `use_custom_label` is determined
- [x] Remove the `resume_from_cache and custom_root_exists` condition
- [x] Ensure `custom_tool_set` is ONLY used when `custom_pub2tools_biotools_json` is not null
- [x] Update `explicit_input` variable usage throughout

### 4. Update documentation
- [x] Update `CONFIG.md` with new parameter name and behavior
- [x] Update `README.md` quick reference table
- [x] Add migration notes for users with existing configs
- [x] Document that existing `custom_tool_set` directories won't be auto-selected

### 5. Update tests
- [x] Update test fixtures in `tests/contract/test_cli_config_integration.py`
- [x] Update test assertions in `tests/unit/test_cli_main.py`
- [x] Update variable names in `tests/unit/test_cli_report_csv.py`
- [x] Add new test case verifying custom_tool_set is NOT used when parameter is null with resume flags
- [x] Add new test case verifying date-based folder IS used with resume flags and null custom input

### 6. Update example configurations
- [x] Update `myconfig.yaml` with new parameter name
- [x] Check for any other example configs in repository

### 7. Update environment variable handling
- [x] Keep `BIOTOOLS_ANNOTATE_INPUT` and `BIOTOOLS_ANNOTATE_JSON` as fallbacks
- [x] Document the precedence order: CLI flag > config parameter > env vars

## Validation
- [x] Run full test suite: `pytest -q`
- [x] Test with `custom_pub2tools_biotools_json: null` and `resume_from_enriched: true` → should use date-based folder
- [x] Test with `custom_pub2tools_biotools_json: "path/to/file.json"` → should use `custom_tool_set`
- [x] Test CLI help shows new parameter: `python -m biotoolsllmannotate run --help`
- [x] Verify existing `out/custom_tool_set/` is not auto-selected during resume

## Dependencies
- No external dependencies
- All tasks can be executed in parallel after task 1 (config schema update)

## Rollback Plan
If issues arise, revert commits in reverse order. The change is largely mechanical and low-risk.
