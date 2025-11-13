# Design: Single Pub2Tools Output Folder

## Architecture Overview

The change affects two primary components:

1. **`pub2tools_client.py`**: Pub2Tools CLI wrapper that invokes the external pub2tools JAR
2. **`cli/run.py`**: Main pipeline orchestrator that searches for and consumes Pub2Tools outputs

## Current Behavior

### Pub2Tools Client Flow

```python
# pub2tools_client.py:233-236
range_prefix = f"range_{from_date}_to_{to_date_str}"
unique_suffix = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
base_dir = Path("out/pub2tools")
output_dir = base_dir / f"{range_prefix}_{unique_suffix}"  # PROBLEM: Always unique
```

Every invocation creates a new timestamped directory under `out/pub2tools/`.

### Pipeline Resume Flow

```python
# cli/run.py:1571-1578
search_roots = [
    time_period_root / "pub2tools",           # e.g., out/range_2025-01-01_to_2025-01-15/pub2tools/
    time_period_root / "pipeline" / "pub2tools",
    time_period_root,
]
for root in search_roots:
    # Search for to_biotools.json in these locations
```

The resume logic searches multiple locations but doesn't account for timestamped subfolder names in `out/pub2tools/`.

## Proposed Changes

### 1. Remove Timestamp Suffix

**File**: `src/biotoolsllmannotate/ingest/pub2tools_client.py`

```python
# BEFORE (lines 233-236)
range_prefix = f"range_{from_date}_to_{to_date_str}"
unique_suffix = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
base_dir = Path("out/pub2tools")
output_dir = base_dir / f"{range_prefix}_{unique_suffix}"

# AFTER
range_prefix = f"range_{from_date}_to_{to_date_str}"
base_dir = Path("out/pub2tools")
output_dir = base_dir / range_prefix  # No timestamp suffix
```

**Rationale**: The date range already uniquely identifies the query scope. Timestamps add no semantic value and create clutter.

### 2. Ensure Idempotent Overwrites

**File**: `src/biotoolsllmannotate/ingest/pub2tools_client.py`

The existing code already handles this correctly:

```python
# Lines 237-242
output_dir.mkdir(parents=True, exist_ok=True)  # OK to reuse existing dir
existing_to_biotools = output_dir / "to_biotools.json"
try:
    if existing_to_biotools.exists():
        existing_to_biotools.unlink()  # Delete old output before running
except OSError:
    pass
```

**No changes needed** in overwrite logic—it already deletes old outputs before writing new ones.

### 3. Update Resume Search Logic (Optional Enhancement)

**File**: `src/biotoolsllmannotate/cli/run.py`

Current search locations:
```python
search_roots = [
    time_period_root / "pub2tools",           # out/range_2025-01-01_to_2025-01-15/pub2tools/
    time_period_root / "pipeline" / "pub2tools",
    time_period_root,
]
```

**Optional addition** to also check the global pub2tools cache:
```python
search_roots = [
    time_period_root / "pub2tools",
    time_period_root / "pipeline" / "pub2tools",
    time_period_root,
    Path("out/pub2tools") / time_period_label,  # NEW: Check global cache
]
```

This allows the pipeline to discover Pub2Tools outputs even when resuming from a different time-period folder.

## Data Flow Diagram

### Before (Current)
```
User runs pipeline with --from-date 2025-01-01 --to-date 2025-01-15

pub2tools_client.py
  ├─ Generates: out/pub2tools/range_2025-01-01_to_2025-01-15_20251111T162353Z/
  └─ Copies to:  out/range_2025-01-01_to_2025-01-15/pub2tools/to_biotools.json

User runs again (same date range)
  ├─ Generates: out/pub2tools/range_2025-01-01_to_2025-01-15_20251111T180805Z/  # NEW FOLDER
  └─ Copies to:  out/range_2025-01-01_to_2025-01-15/pub2tools/to_biotools.json  # Overwrites

Result: Two pub2tools folders for identical date range
```

### After (Proposed)
```
User runs pipeline with --from-date 2025-01-01 --to-date 2025-01-15

pub2tools_client.py
  ├─ Generates: out/pub2tools/range_2025-01-01_to_2025-01-15/  # Canonical folder
  └─ Copies to:  out/range_2025-01-01_to_2025-01-15/pub2tools/to_biotools.json

User runs again (same date range)
  ├─ Reuses:    out/pub2tools/range_2025-01-01_to_2025-01-15/  # SAME FOLDER
  └─ Overwrites internal files before running Pub2Tools CLI
  └─ Copies to:  out/range_2025-01-01_to_2025-01-15/pub2tools/to_biotools.json  # Overwrites

Result: One pub2tools folder per date range
```

## Edge Cases & Handling

### 1. Concurrent Runs (Same Date Range)
**Scenario**: Two pipeline instances run simultaneously with identical date parameters

**Risk**: File system race conditions in `out/pub2tools/range_X_to_Y/`

**Mitigation**: 
- Document that concurrent runs with identical date ranges are unsupported
- No locking mechanism added (over-engineering for rare case)
- Users should run sequentially or use different date ranges

### 2. Resume from Old Timestamped Folder
**Scenario**: Existing timestamped folders from previous runs (`range_X_to_Y_<timestamp>/`)

**Handling**:
- Leave old folders untouched
- New runs create canonical folders only
- Resume logic may still find old timestamped folders via glob patterns
- Users can manually delete old folders after verifying new behavior

### 3. Pub2Tools CLI Failure Mid-Run
**Scenario**: Pub2Tools CLI crashes after partial file writes

**Handling**:
- Existing code already deletes `to_biotools.json` before running (line 238-242)
- Other intermediate files may remain stale
- Next run will overwrite them
- No additional cleanup logic needed

## Testing Strategy

### Unit Tests
- `test_pub2tools_client.py`: Verify output folder naming strips timestamps
- Mock `datetime.now()` to ensure deterministic folder names

### Integration Tests
- Run pipeline twice with identical date ranges
- Assert second run reuses the same `out/pub2tools/range_*/` folder
- Verify `to_biotools.json` is overwritten, not duplicated

### Manual Testing
1. Delete `out/pub2tools/` directory
2. Run: `python -m biotoolsllmannotate --from-date 2025-01-01 --to-date 2025-01-15`
3. Verify folder: `out/pub2tools/range_2025-01-01_to_2025-01-15/` exists (no timestamp)
4. Run same command again
5. Verify: Same folder reused, no `_20251113T...` suffix created
6. Check: `to_biotools.json` timestamp reflects second run

## Rollback Plan

If issues arise:
1. Revert the single-line change in `pub2tools_client.py` (restore timestamp suffix)
2. No data loss: Main pipeline outputs (`out/range_*/`) are unaffected
3. Old timestamped folders remain valid for resume operations

## Documentation Updates

- **README.md**: Update "Running the Pipeline" section to mention canonical folder reuse
- **CONFIG.md**: Note that Pub2Tools outputs are ephemeral and overwritten per date range
- **Code comments**: Add comment explaining the canonical naming strategy in `pub2tools_client.py`
