# Proposal: Validate Payload Entries Against bio.tools API

## Why

Currently, after scoring and checking tool presence in bio.tools (using local or cached registry data), the pipeline does not verify that the payload entries are consistent with the live bio.tools registry. This can lead to discrepancies if the local snapshot is outdated or incomplete.

## What Changes

- After the scoring and registry membership checks, the pipeline SHALL validate each payload entry (by bio.tools ID) using the live bio.tools API.
- If a tool is present in the payload and claims to exist in bio.tools, the pipeline SHALL fetch the corresponding record from the API and validate key fields (e.g., ID, name, status, etc.).
- If a tool is missing or the API returns an error, the pipeline SHALL log a warning and optionally flag the entry for review.
- This validation step SHALL be optional (enabled by config/flag) to avoid unnecessary API load during batch runs or offline mode.

## Success Criteria

- The pipeline performs live validation of payload entries against the bio.tools API after scoring and registry checks.
- Discrepancies or missing records are logged and optionally flagged in the output.
- The feature is covered by tests and documented in the CLI help and configuration reference.
