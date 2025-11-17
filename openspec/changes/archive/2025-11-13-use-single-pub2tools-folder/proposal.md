# Proposal: Use Single Pub2Tools Folder Per Date Range

## Why

Users are experiencing disk space waste and folder clutter from the Pub2Tools CLI wrapper creating a new timestamped folder for every invocation, even when querying the same date range repeatedly. This makes it difficult to locate the "latest" run outputs and complicates resume logic. The timestamp suffix provides no semantic value since the date range parameters already uniquely identify the query scope.

This change simplifies the folder structure to use one canonical folder per date range (`out/pub2tools/range_<from>_to_<to>`), making outputs predictable and easier to manage while reducing disk usage.

## Problem Statement

Currently, the Pub2Tools CLI client creates a new uniquely timestamped folder for every invocation, resulting in proliferation of nearly identical directories:

```
out/pub2tools/
  range_2025-01-01_to_2025-01-15_20251111T162353Z/
  range_2025-01-01_to_2025-01-15_20251111T180805Z/
  range_2025-01-01_to_2025-01-15_20251111T180824Z/
  range_2025-01-01_to_2025-01-15_20251111T181007Z/
  ...
```

This happens because `pub2tools_client.py` appends a timestamp suffix (`datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")`) to every output directory, even when the date range parameters are identical. Multiple runs for the same date range produce redundant folders that waste disk space and complicate manual inspection of outputs.

**User Impact:**
- Disk space waste from duplicate intermediate files
- Confusion when locating the "latest" run for a given date range
- Manual cleanup burden to remove outdated timestamped folders
- Harder to implement resume logic when folder names are unpredictable

## Proposed Solution

Replace the individually keyed timestamped folders (`range_<from>_to_<to>_<timestamp>`) with a single canonical folder per date range (`range_<from>_to_<to>`). The Pub2Tools CLI client will:

1. **Reuse the same folder** for repeat invocations with identical date parameters
2. **Overwrite existing outputs** in that folder to reflect the most recent run
3. **Simplify resume logic** by using predictable paths

### Key Changes

- **Remove timestamp suffix** from `pub2tools_client.py` output directory naming
- **Update resume logic** in `cli/run.py` to locate the canonical date-range folder
- **Document behavior** in user-facing docs and code comments

### Non-Goals

- This change does NOT affect the main pipeline output folders under `out/range_*/` (those remain as-is)
- This change does NOT introduce versioning or archival of old Pub2Tools runs
- This change does NOT modify the Pub2Tools CLI itself (only our wrapper client)

## Impact Assessment

### Benefits
- **Simpler folder structure**: One folder per date range instead of N folders
- **Predictable paths**: Resume logic can reliably find `out/pub2tools/range_<from>_to_<to>/to_biotools.json`
- **Reduced disk usage**: No duplicate intermediate Pub2Tools outputs
- **Easier debugging**: Clear "current" state for each date range

### Risks
- **Loss of run history**: Previous runs' intermediate Pub2Tools outputs will be overwritten
  - *Mitigation*: The main pipeline folders (`out/range_*/`) preserve full run history; Pub2Tools intermediates are ephemeral
- **Concurrent run conflicts**: Two simultaneous runs for the same date range could collide
  - *Mitigation*: This is a rare edge case; users typically run sequentially

### Compatibility
- **Breaking change**: Users relying on timestamped folder names in scripts will need to update
- **Migration**: Existing timestamped folders can remain; new runs create canonical folders

## Alternatives Considered

1. **Keep timestamp but use symlink**: Create `range_<from>_to_<to>` as a symlink to the latest timestamped folder
   - *Rejected*: Adds complexity and doesn't solve disk usage issue

2. **Implement cleanup policy**: Automatically delete old timestamped folders after N days
   - *Rejected*: Doesn't solve the root issue of unnecessary folder creation

3. **Add run ID to main pipeline folders**: Make main output folders uniquely timestamped
   - *Rejected*: User explicitly wants to avoid individually keyed folders everywhere

## Open Questions

1. Should we preserve the last N timestamped runs instead of immediate overwrite?
   - *Recommendation*: No, keep it simple. Users can manually backup if needed.

2. Should the change apply retroactively to existing timestamped folders?
   - *Recommendation*: No, leave existing folders as-is. Only new runs use canonical names.

## Success Criteria

- Running the pipeline twice with `--from-date 2025-01-01 --to-date 2025-01-15` produces outputs in the same `out/pub2tools/range_2025-01-01_to_2025-01-15/` folder
- Second run overwrites `to_biotools.json` from the first run
- Resume logic successfully locates the canonical folder
- No timestamped suffixes appear in new Pub2Tools output folders
- Existing CLI tests pass with minimal updates
