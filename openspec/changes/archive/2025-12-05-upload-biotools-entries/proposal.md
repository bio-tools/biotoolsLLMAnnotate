# Upload bio.tools Entries

## Problem

Users currently generate validated bio.tools payloads (`biotools_add.json`, `biotools_review.json`) but have no automated way to submit them to the bio.tools registry. The workflow stops at file generation, requiring manual copy-paste into the bio.tools web interface for each entry. This creates friction for batch annotations and prevents seamless end-to-end automation.

## Proposed Solution

Add upload capabilities to the CLI pipeline using the bio.tools REST API. Users will be able to:

1. **Upload new entries** - POST validated payloads to `https://bio.tools/api/tool/` with authentication
2. **Skip existing entries** - Check if entry exists and skip if already present
3. **Resume interrupted uploads** - Track upload state in assessment.csv to support resume

The implementation will leverage existing infrastructure:
- **Authentication**: Reuse `.bt_token` file and `read_biotools_token()` 
- **API client**: Extend `biotools_api.py` with upload functions (POST only)
- **Validation**: Already validates payloads before upload via `validate_biotools_entry()`
- **CLI integration**: Add `--upload` flag to existing pipeline

## Why This Approach

**Leverages existing auth**: The `.bt_token` file and token reading logic already exist for validation API. No new auth mechanism needed.

**Minimal disruption**: Upload is opt-in via `--upload` flag. Default behavior (file generation) unchanged. Users control when entries go live. Conflicts with existing entries are skipped.

**Resumable by design**: Stores upload status in assessment.csv `upload_status` column. Interrupted batch uploads can resume without re-processing.

**API-first**: Uses official bio.tools REST API POST endpoint, ensuring compatibility with registry schema. No update operations to reduce complexity.

**Separation of concerns**: 
- `biotools_api.py` handles HTTP POST requests and authentication
- `cli/run.py` orchestrates workflow and user interaction
- `assessment.csv` tracks state across resume boundaries

## Impact

- Enables end-to-end automation for bio.tools annotation workflows
- Reduces manual effort for batch tool submissions
- Provides audit trail via upload status tracking in CSV
- Maintains backward compatibility (upload is opt-in)

## Risks

- **API rate limits**: bio.tools may throttle high-volume uploads. Mitigation: Add exponential backoff and batch delay configuration.
- **Schema drift**: bio.tools schema changes could break payloads. Mitigation: Validation step catches issues pre-upload.
- **Token security**: Token file must be protected. Mitigation: Already in .gitignore; document security practices in README.
- **Duplicate entries**: Tool already exists on bio.tools. Mitigation: Check existence first and skip (no update), user must resolve conflicts manually.

## Alternatives Considered

1. **Web UI automation (Selenium)** - Brittle, breaks with UI changes, requires browser runtime
2. **Manual upload instructions** - Current state, doesn't scale for batch operations  
3. **Separate upload script** - Duplicates auth/API logic, users must manage two tools
4. **Allow update via PUT/PATCH** - Considered but rejected to keep scope focused: users can manually update existing entries via web UI

## Success Metrics

- Users can upload new validated entries with single command
- Existing entries are detected and skipped (no errors)
- Upload failures provide actionable error messages
- Resume workflow correctly skips already-uploaded entries
- Documentation covers token setup and troubleshooting
- **NEW**: Final report CSV summarizes all upload outcomes with direct bio.tools URLs for successful uploads

## Additional Enhancement: Upload Report CSV

In addition to tracking upload status in `assessment.csv`, users will receive a dedicated `upload_report.csv` file containing:
- **biotools_id**: Tool identifier
- **status**: "uploaded", "failed", or "skipped"
- **bio_tools_url**: Direct link to tool on bio.tools (populated for successful uploads)
- **error**: Error message if failed
- **response_code**: HTTP status code from API
- **timestamp**: When upload was attempted

This provides a clean, actionable summary file for batch uploads without cluttering the assessment CSV.
