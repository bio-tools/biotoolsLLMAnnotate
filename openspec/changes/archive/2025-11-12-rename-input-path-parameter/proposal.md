# Proposal: Rename input-path Parameter

## Problem Statement
The current `pipeline.input_path` configuration parameter has an ambiguous name that doesn't clearly communicate its purpose. Additionally, the logic for determining when to use the `custom_tool_set` output directory has an unintended "sticky" behavior: once `out/custom_tool_set/` exists, any run with a resume flag will continue using that directory even when the user expects a date-based folder.

This creates confusion:
1. Users with `input_path: null` and `resume_from_enriched: true` unexpectedly get `out/custom_tool_set/` instead of `out/range_YYYY-MM-DD_to_YYYY-MM-DD/`
2. The parameter name doesn't clearly indicate it should point to a Pub2Tools `to_biotools.json` export
3. The resume-based triggering of `custom_tool_set` conflicts with the original intent (custom input files only)

## Proposed Solution
1. Rename `pipeline.input_path` to `pipeline.custom_pub2tools_biotools_json` to clearly communicate its purpose
2. Change the `custom_tool_set` directory logic to ONLY trigger when this parameter is explicitly set (not null)
3. Remove the "sticky" behavior where resume flags cause `custom_tool_set` to be reused

This ensures:
- Clear semantics: the parameter name reflects what it accepts (a Pub2Tools JSON export)
- Predictable behavior: date-based folders are used for date-based queries, custom folders only for custom inputs
- No sticky behavior: resume flags don't accidentally perpetuate `custom_tool_set` usage

## Impact Assessment
- **Breaking Change**: Users with `input_path` in their configs must rename it to `custom_pub2tools_biotools_json`
- **Behavior Change**: Existing `out/custom_tool_set/` directories will stop being auto-selected during resume operations
- **Migration Path**: Configuration validation can warn about deprecated `input_path` and suggest the new name

## Related Capabilities
- `cli-pipeline`: Pipeline stage progression and candidate ingestion order

## Success Criteria
1. Configuration accepts `custom_pub2tools_biotools_json` parameter
2. `custom_tool_set` directory is used ONLY when `custom_pub2tools_biotools_json` is not null
3. Resume flags with date-based queries use `out/range_YYYY-MM-DD_to_YYYY-MM-DD/`
4. All tests pass with the renamed parameter
5. Documentation reflects the new parameter name and behavior
