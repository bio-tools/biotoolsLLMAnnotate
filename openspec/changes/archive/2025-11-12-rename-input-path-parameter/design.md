# Design: Custom Input Parameter Clarification

## Context
The pipeline supports multiple input sources: date-based Pub2Tools fetching, resuming from cached exports, or loading a custom Pub2Tools JSON export. The output directory naming should reflect the input source:
- Date-based queries → `out/range_YYYY-MM-DD_to_YYYY-MM-DD/`
- Custom input files → `out/custom_tool_set/`

Currently, the logic has an unintended side effect where resume flags can perpetuate `custom_tool_set` usage even when the user intends a date-based query.

## Architecture Decision

### Current Flow
```python
explicit_input = input_path or os.environ.get("BIOTOOLS_ANNOTATE_INPUT")
has_explicit_input = bool(explicit_input)
resume_from_cache = (resume_from_enriched or resume_from_pub2tools or resume_from_scoring)
use_custom_label = has_explicit_input or (resume_from_cache and custom_root_exists)
```

**Problem**: The `resume_from_cache and custom_root_exists` condition creates sticky behavior.

### Proposed Flow
```python
explicit_input = custom_pub2tools_biotools_json or os.environ.get("BIOTOOLS_ANNOTATE_INPUT")
has_explicit_input = bool(explicit_input)
use_custom_label = has_explicit_input  # Remove resume-based triggering
```

**Benefit**: `custom_tool_set` is used ONLY when a custom input is explicitly provided.

## Trade-offs

### Option A: Remove sticky behavior entirely (CHOSEN)
**Pros**:
- Clear, predictable semantics
- Date-based queries always use date-based folders
- No hidden state dependencies

**Cons**:
- Users with existing `custom_tool_set` resume workflows need to explicitly provide the input file
- Slightly more verbose for truly custom input workflows

### Option B: Add a separate config flag `force_custom_label`
**Pros**:
- Preserves backward compatibility
- Allows explicit control

**Cons**:
- Adds complexity
- Another configuration parameter to understand
- Still doesn't fix the ambiguous naming

## Migration Strategy

Users with existing workflows that rely on sticky `custom_tool_set` behavior will need to:

1. **If using custom input files**: Explicitly set `custom_pub2tools_biotools_json: "path/to/file.json"` in config
2. **If using date-based queries with resume**: Remove or verify `custom_pub2tools_biotools_json: null` and the system will use date-based folders

We'll add clear logging when the old parameter name is detected and suggest the new name.

## Implementation Notes

### Files to Modify
1. `src/biotoolsllmannotate/config.py` - default config schema
2. `src/biotoolsllmannotate/cli/main.py` - CLI parameter definition
3. `src/biotoolsllmannotate/cli/run.py` - directory naming logic
4. Documentation files - CONFIG.md, README.md
5. Test files - update parameter references

### Backward Compatibility
- Keep environment variable names unchanged (`BIOTOOLS_ANNOTATE_INPUT`, `BIOTOOLS_ANNOTATE_JSON`)
- Add deprecation warning if old config parameter is detected
- No changes to output file formats or data structures

## Validation Strategy

Test scenarios:
1. `custom_pub2tools_biotools_json: null` + `resume_from_enriched: true` → uses date-based folder
2. `custom_pub2tools_biotools_json: "file.json"` → uses `custom_tool_set`
3. `custom_pub2tools_biotools_json: null` + date range → uses date-based folder
4. Environment variable set → uses `custom_tool_set`
5. Existing `out/custom_tool_set/` present but parameter null → ignores directory, uses date-based folder
