# Tasks: Use Single Pub2Tools Folder Per Date Range

## Implementation Tasks

- [x] **Remove timestamp suffix from Pub2Tools output directory naming**
  - File: `src/biotoolsllmannotate/ingest/pub2tools_client.py`
  - Lines: ~233-236
  - Change: Remove `unique_suffix` variable and timestamp concatenation
  - Validation: Unit test verifies folder name is `range_<from>_to_<to>` without timestamp
  - Dependencies: None

- [x] **Add code comment explaining canonical folder naming**
  - File: `src/biotoolsllmannotate/ingest/pub2tools_client.py`
  - Location: Above the `range_prefix` variable assignment
  - Content: Document that folder is reused across runs with identical date ranges
  - Validation: Code review
  - Dependencies: Previous task

- [x] **Update docstring for `fetch_candidates_all` function**
  - File: `src/biotoolsllmannotate/ingest/pub2tools_client.py`
  - Location: Function docstring starting at line ~207
  - Content: Document that outputs are written to `out/pub2tools/range_<from>_to_<to>/` and overwritten on subsequent runs
  - Validation: Docstring review
  - Dependencies: None (can be done in parallel)

- [x] **Add optional global pub2tools cache to resume search paths**
  - File: `src/biotoolsllmannotate/cli/run.py`
  - Lines: ~1571-1578 (search_roots list)
  - Change: Append `Path("out/pub2tools") / time_period_label` to search_roots
  - Validation: Integration test verifies resume finds cached Pub2Tools output
  - Dependencies: None (optional enhancement, can be skipped)

## Testing Tasks

- [ ] **Create unit test for canonical folder naming**
  - File: `tests/unit/test_pub2tools_client.py` (create if not exists)
  - Test: Mock `fetch_candidates_all` call, verify output_dir is `out/pub2tools/range_2025-01-01_to_2025-01-15` (no timestamp)
  - Validation: `pytest tests/unit/test_pub2tools_client.py -v`
  - Dependencies: Implementation task 1

- [ ] **Create integration test for folder reuse**
  - File: `tests/integration/test_pub2tools_folder_reuse.py` (create new)
  - Test: 
    1. Run pipeline with date range X
    2. Record folder path and file timestamp
    3. Run pipeline again with same date range
    4. Verify same folder path used
    5. Verify `to_biotools.json` timestamp is newer
  - Validation: `pytest tests/integration/test_pub2tools_folder_reuse.py -v`
  - Dependencies: Implementation tasks complete

- [x] **Update existing CLI integration tests**
  - File: `tests/integration/test_end_to_end.py`
  - Change: Update any assertions that check for timestamped folder names
  - Validation: `pytest tests/integration/ -v`
  - Dependencies: Implementation tasks complete

## Documentation Tasks

- [x] **Update README.md with folder reuse behavior**
  - File: `README.md`
  - Section: "Running the Pipeline"
  - Content: Add note that Pub2Tools outputs are cached in `out/pub2tools/range_*/` and reused for identical date ranges
  - Validation: Documentation review
  - Dependencies: None (can be done in parallel)

- [x] **Update CONFIG.md with Pub2Tools folder behavior**
  - File: `CONFIG.md`
  - Section: "Pub2Tools Configuration" (or create new section)
  - Content: Document that `pub2tools.timeout` affects cached output location and that outputs are ephemeral per date range
  - Validation: Documentation review
  - Dependencies: None (can be done in parallel)

- [ ] **Add migration note for users with existing timestamped folders**
  - File: `README.md` or `CHANGELOG.md`
  - Content: Note that old timestamped folders (`range_*_<timestamp>`) can be manually deleted; new runs create canonical folders only
  - Validation: Documentation review
  - Dependencies: None

## Validation Tasks

- [x] **Manual smoke test: Run pipeline twice with same date range**
  - Steps:
    1. Delete `out/pub2tools/` directory
    2. Run: `python -m biotoolsllmannotate --from-date 2025-01-01 --to-date 2025-01-15`
    3. Verify folder: `out/pub2tools/range_2025-01-01_to_2025-01-15/` exists (no timestamp suffix)
    4. Note timestamp of `to_biotools.json`
    5. Run same command again
    6. Verify: Same folder reused, `to_biotools.json` timestamp is newer
  - Validation: Manual verification
  - Dependencies: All implementation tasks

- [ ] **Manual smoke test: Resume from cached Pub2Tools output**
  - Steps:
    1. Run pipeline with `--from-date 2025-01-01 --to-date 2025-01-15`
    2. Delete `out/range_2025-01-01_to_2025-01-15/pub2tools/to_biotools.json`
    3. Run with `--resume-from-pub2tools` and same date range
    4. Verify pipeline finds `out/pub2tools/range_2025-01-01_to_2025-01-15/to_biotools.json` (if optional search path added)
  - Validation: Manual verification
  - Dependencies: All implementation tasks including optional enhancement

- [x] **Run full test suite**
  - Command: `PYTHONPATH=src pytest -v`
  - Validation: All tests pass (84/84 or higher)
  - Dependencies: All implementation and testing tasks

## Cleanup Tasks (Optional)

- [ ] **Provide utility script to clean old timestamped folders**
  - File: `scripts/cleanup_old_pub2tools_folders.py` (create new)
  - Function: Find and optionally delete folders matching `out/pub2tools/range_*_<timestamp>/`
  - Safety: Require user confirmation before deletion
  - Validation: Manual testing
  - Dependencies: None (optional convenience)

## Task Sequencing

**Critical path** (must be done in order):
1. Implementation task 1 (remove timestamp suffix)
2. Testing task 1 (unit test for canonical naming)
3. Testing task 2 (integration test for folder reuse)
4. Validation task 1 (manual smoke test)

**Parallel workstreams**:
- Documentation tasks can proceed independently
- Code comment tasks can be done alongside implementation
- Optional cleanup script can be developed separately

**Recommended order**:
1. Implementation tasks 1-3 (core changes + comments)
2. Testing tasks 1-2 (unit + integration tests)
3. Testing task 3 (update existing tests)
4. Documentation tasks 1-3 (README, CONFIG, migration notes)
5. Validation tasks 1-2 (manual smoke tests)
6. Validation task 3 (full test suite)
7. Optional: Implementation task 4 + cleanup script (enhancements)
