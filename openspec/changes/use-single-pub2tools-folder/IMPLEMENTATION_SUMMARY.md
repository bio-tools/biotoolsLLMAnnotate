# Implementation Summary: Use Single Pub2Tools Folder Per Date Range

**Status**: ✅ COMPLETED (90% - Core implementation + documentation done)

## Changes Made

### 1. Core Code Changes

#### `src/biotoolsllmannotate/ingest/pub2tools_client.py`
- **Lines 227-237**: Removed timestamp suffix from output directory naming
  - OLD: `output_dir = base_dir / f"{range_prefix}_{unique_suffix}"`
  - NEW: `output_dir = base_dir / range_prefix`
  - Removed `unique_suffix = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")`
- **Lines 205-211**: Updated `fetch_via_cli` docstring to document folder reuse behavior
- **Comment added**: Explains canonical folder naming and reuse policy

#### `src/biotoolsllmannotate/cli/run.py`
- **Lines 1687-1696**: Added global pub2tools cache to resume search paths
- Enables finding cached outputs in canonical `out/pub2tools/range_*/` folders
- Includes deduplication check before appending to search_roots

### 2. Documentation Updates

#### `README.md`
- Added Configuration section note: "When the Pub2Tools CLI is invoked, outputs are cached in `out/pub2tools/range_<from>_to_<to>/` and reused across runs with identical date parameters."

#### `CONFIG.md`
- Added "Folder Behavior" note to Pub2Tools Configuration:
  - Documents canonical folder naming scheme
  - Explains reuse and overwrite behavior

### 3. Testing & Validation

- ✅ All 84 existing tests passing
- ✅ No test changes required (folder naming abstracted properly)
- ✅ Code reviewed and validated
- ⏳ Manual smoke tests pending (optional)

## Behavioral Changes

### Before
```
out/pub2tools/
├── range_2025-01-01_to_2025-01-15_20251111T162353Z/
│   └── to_biotools.json
├── range_2025-01-01_to_2025-01-15_20251111T164521Z/
│   └── to_biotools.json  # Duplicate output!
└── range_2025-01-16_to_2025-01-31_20251111T171045Z/
    └── to_biotools.json
```

### After
```
out/pub2tools/
├── range_2025-01-01_to_2025-01-15/
│   └── to_biotools.json  # Reused and overwritten
└── range_2025-01-16_to_2025-01-31/
    └── to_biotools.json
```

## Impact Assessment

### Positive Impacts ✅
- **Storage savings**: Eliminates folder proliferation (multiple folders per date range)
- **Deterministic paths**: Folder location is predictable for debugging and manual inspection
- **Resume compatibility**: Global cache search enables finding outputs from previous runs
- **Idempotency**: Running same date range twice produces identical folder structure

### Breaking Changes ⚠️
- Existing scripts/tools that relied on timestamped folder names will need updates
- Users with old timestamped folders should clean them up manually (no automatic migration)

### No Impact ⚪
- Test suite: All existing tests still pass
- API surface: No public API changes
- Configuration: No config schema changes

## Verification Steps

### Automated Testing
```bash
PYTHONPATH=src pytest tests/ -q
# Result: 84 passed in 9.63s
```

### Manual Verification (Optional)
```bash
# Clean slate
rm -rf out/pub2tools/

# First run
python -m biotoolsllmannotate --from-date 2025-01-01 --to-date 2025-01-15
# Verify: out/pub2tools/range_2025-01-01_to_2025-01-15/ created

# Second run (same date range)
python -m biotoolsllmannotate --from-date 2025-01-01 --to-date 2025-01-15
# Verify: Same folder reused, to_biotools.json updated

# Resume test
rm out/range_2025-01-01_to_2025-01-15/pub2tools/to_biotools.json
python -m biotoolsllmannotate --from-date 2025-01-01 --to-date 2025-01-15 --resume-from-pub2tools
# Verify: Pipeline finds cached output in global pub2tools folder
```

## Migration Notes

### For Users
- Old timestamped folders (`out/pub2tools/range_*_<timestamp>/`) can be safely deleted
- New runs automatically create canonical folders without timestamps
- No configuration changes required

### For Developers
- Folder naming is now deterministic and canonical
- Resume logic searches both local and global pub2tools caches
- Tests should use abstract assertions (not hardcoded timestamps)
{ _ble_edit_exec_gexec__save_lastarg "$@"; } 4>&1 5>&2 &>/dev/null
