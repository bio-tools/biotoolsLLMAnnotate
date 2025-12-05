# OpenSpec Proposal: upload-biotools-entries

## Summary

Created comprehensive OpenSpec proposal for adding bio.tools upload and revision capabilities to the CLI pipeline.

## Proposal Location

`openspec/changes/upload-biotools-entries/`

## Files Created

1. **proposal.md** - Problem statement, solution approach, rationale, risks, and alternatives
2. **tasks.md** - 6 implementation phases with 59 tasks and 12-15 hour estimate
3. **design.md** - Architecture diagrams, API signatures, data flows, error handling, and configuration
4. **specs/biotools-upload/spec.md** - 11 requirements with 40+ scenarios

## Validation Status

✅ **Valid** - Passed `openspec validate upload-biotools-entries --strict`

## Key Requirements (11)

1. **Create New Entries via API** - POST validated entries, handle 201/409/400 responses
2. **Check Existence Before Upload** - Query API to avoid duplicates, skip existing entries
3. **Token-Based Authentication** - Read `.bt_token`, abort if missing, handle 401
4. **Resume After Failure** - Track status in CSV, skip uploaded, retry failed
5. **Error Handling and Retries** - Exponential backoff, no retry on 4xx, rate limit handling
6. **Upload Results Reporting** - Console summary, JSONL log, and CSV detailed results
7. **Upload Report CSV with Tool URLs** - **NEW** - Dedicated CSV with bio.tools URLs for successful uploads
8. **Configuration and Defaults** - Opt-in by default, CLI overrides config, customizable retries
9. **Separation from Payload Generation** - Upload is optional phase, doesn't modify generation

## Implementation Phases

### Phase 1: API Functions (2-3 hours)
- Add `create_biotools_entry()` for POST
- Add `update_biotools_entry()` for PUT
- Implement retry logic with exponential backoff

### Phase 2: CLI Integration (3-4 hours)
- Add `--upload` and `--upload-mode` flags
- Orchestrate upload workflow
- Implement resume support
- Progress reporting

### Phase 3: Configuration (1 hour)
- Add upload config schema
- Token validation at startup

### Phase 4: Testing (3-4 hours)
- Unit tests for API functions
- Integration tests with mocks
- Contract tests (requires dev token)

### Phase 5: Documentation (1-2 hours)
- README upload section
- BIOTOOLS_API_VALIDATION.md updates
- CSV column documentation

### Phase 6: Validation & Cleanup (1 hour)
- Full test suite
- Linting and formatting
- Manual testing checklist
- OpenSpec validation

## Architecture Highlights

### Upload Flow
```
CLI Entry → Existing Pipeline → Upload Phase → bio.tools API
                                    ↓
                            assessment.csv (upload_status)
                            upload_results.jsonl
```

### API Functions
- `create_biotools_entry()` - POST /api/tool/
- `update_biotools_entry()` - PUT /api/tool/{id}
- `fetch_biotools_entry()` - GET /api/tool/{id} (existing)

### Status Tracking

Two CSV files track upload outcomes:
- **assessment.csv**: Includes `upload_status` column with values: pending, uploaded, failed, skipped
- **upload_report.csv** (NEW): Dedicated summary with bio.tools API URLs for successful uploads
  - Columns: biotoolsID, status, bio_tools_url, error, response_code, timestamp
  - bio_tools_url: `{api_base}/{biotoolsID}` (e.g., `https://bio.tools/api/tool/tool-name`) for successful uploads, empty for failed/skipped
  - Provides clean, actionable summary distinct from full assessment data

Also logs detailed JSONL output to `upload_results.jsonl` with per-entry tracking.

**Note**: The `bio_tools_url` field contains the API endpoint URL (e.g., `https://bio.tools/api/tool/tool-name`) rather than the user-facing bio.tools page URL. This provides direct access to the tool's API representation.

### Error Handling
- **5xx errors**: Retry with exponential backoff (1s, 2s, 4s)
- **4xx errors**: No retry, log error
- **429 Rate Limit**: Backoff and retry
- **401 Unauthorized**: Abort batch, check token

## Configuration Schema

```yaml
pipeline:
  upload:
    enabled: false  # Opt-in
    mode: "both"    # "new-only" | "update-only" | "both"
    retry_attempts: 3
    retry_delay: 1.0
    batch_delay: 0.5
    log_file: "upload_results.jsonl"
```

## CLI Usage Examples

### Upload new and update existing
```bash
biotoolsllmannotate --upload --output-dir ./output
```

### Upload only new entries
```bash
biotoolsllmannotate --upload --upload-mode=new-only
```

### Resume interrupted upload
```bash
biotoolsllmannotate --resume-from-scoring ./output/assessment.csv --upload
```

## Scenarios Covered (40+)

- 3 scenarios for creating new entries (success, conflict, validation error)
- 3 scenarios for checking existence (exists, not exists, auth applied)
- 3 scenarios for token auth (load, abort, unauthorized)
- 3 scenarios for resume (skip uploaded, retry failed, initial pending)
- 3 scenarios for error handling (server retry, no client retry, rate limit)
- 3 scenarios for reporting (console, JSONL, CSV)
- 4 scenarios for upload report CSV with URLs (successful upload, failed, skipped, summary)
- 3 scenarios for config (default, override, retry params)
- 2 scenarios for separation (generate without upload, upload existing)
- Plus additional edge cases and validation scenarios

## Dependencies

- Existing `validate_biotools_entry()` function
- Existing `.bt_token` file support
- `requests` library (already installed)
- CSV writing infrastructure in `cli/run.py`

## Backward Compatibility

- ✅ Default behavior unchanged (upload is opt-in)
- ✅ Existing configs work without modification
- ✅ CSV format extended (new column), existing columns unchanged
- ✅ Resume workflow works with or without upload

## Testing Strategy

- **Unit tests**: Mock requests, test all status codes, verify retry logic
- **Integration tests**: Mock API responses, test full workflow
- **Contract tests**: Real API calls to dev server (skip if no token)

## Security Considerations

- Token in .gitignore (already configured)
- Never log full token (redact in output)
- HTTPS only for API calls
- Validate token exists before batch upload
- Don't leak token in error messages

## Next Steps

1. Begin Phase 1 implementation (API functions)
2. Follow tasks.md checklist
3. Run `openspec validate upload-biotools-entries --strict` after code changes
4. Archive proposal when complete

## Estimated Timeline

**Total**: 12-15 hours

- API: 2-3 hours
- CLI: 3-4 hours
- Config: 1 hour
- Tests: 3-4 hours
- Docs: 1-2 hours
- Validation: 1 hour

## Status

- ✅ Proposal created
- ✅ Validated (strict mode)
- ✅ Implementation complete (59/59 tasks)
- ✅ All tests passing (135/135)
- ✅ Documentation updated
