# Design: bio.tools Upload & Revision

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      CLI Entry Point                         │
│                  (cli/run.py main())                         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ├─ Parse --upload flag
                       ├─ Load config (upload.enabled, retries)
                       ├─ Check .bt_token exists
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Existing Pipeline Phases                        │
│  1. Ingest → 2. Enrich → 3. Assess → 4. Validate → 5. Generate │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ Produces: biotools_add.json, biotools_review.json
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    NEW: Upload Phase                         │
│                  (cli/run.py upload_entries())               │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ├─ Load token with read_biotools_token()
                       ├─ Load payloads from biotools_add.json
                       ├─ For each entry:
                       │   ├─ Check resume: skip if upload_status="uploaded"
                       │   ├─ Check existence (GET)
                       │   ├─ If exists: skip with status "skipped"
                       │   ├─ If new: POST with create_biotools_entry()
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              API Client (biotools_api.py)                    │
│                                                               │
│  create_biotools_entry(entry, api_base, token)              │
│    → POST /api/tool/                                         │
│    → Returns: {success, biotools_id, error}                 │
│                                                               │
│  fetch_biotools_entry(biotools_id, ...) [EXISTING]         │
│    → GET /api/tool/{id}                                      │
│    → Returns: entry dict or None                            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                bio.tools REST API                            │
│   https://bio.tools/api/tool/ (production only)            │
│                                                               │
│   POST /api/tool/           → 201 Created / 409 Conflict    │
│   GET /api/tool/{id}        → 200 OK / 404 Not Found        │
│                                                               │
│   Auth: Authorization: Token {token}                        │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

### Input: Generated Payloads
```json
// biotools_add.json (new entries)
[
  {
    "biotoolsID": "tool-name",
    "name": "Tool Name",
    "description": "...",
    "homepage": "https://...",
    ...
  }
]

// biotools_review.json (entries for update)
[
  {
    "biotoolsID": "existing-tool",
    "name": "Updated Tool",
    ...
  }
]
```

### Output: Upload Results

**Console Summary:**
```
Upload Summary:
  ✓ Uploaded: 8 entries
  ✗ Failed: 2 entries
  ⊘ Skipped: 1 entry (already uploaded)

Failed Entries:
  • tool-xyz: 409 Conflict - Entry already exists
  • tool-abc: 400 Bad Request - Invalid EDAM topic
```

**assessment.csv (new column):**
```csv
manual_decision,id,name,...,include,upload_status
,PMC123,Tool1,...,add,uploaded
,PMC456,Tool2,...,add,failed
,PMC789,Tool3,...,review,uploaded
```

**upload_results.jsonl (detailed log):**
```jsonl
{"biotools_id":"tool1","status":"uploaded","response_code":201,"timestamp":"2024-01-15T10:30:00Z"}
{"biotools_id":"tool2","status":"failed","error":"409 Conflict","timestamp":"2024-01-15T10:30:05Z"}
```

## API Function Signatures

### New Functions in `biotools_api.py`

```python
def create_biotools_entry(
    entry: Dict[str, Any],
    api_base: str = "https://bio.tools/api/tool/",
    token: Optional[str] = None,
    timeout: int = 30,
) -> Dict[str, Any]:
    """
    Create a new bio.tools entry via POST.
    
    Returns:
        {
            "success": bool,
            "biotools_id": str,  # if success
            "error": str,         # if failure
            "status_code": int,   # HTTP status
        }
    """
    pass
```

### Upload Orchestration in `cli/run.py`

```python
def upload_entries(
    add_entries: List[Dict[str, Any]],
    config: Config,
    token: str,
    resume_data: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Upload new bio.tools entries (POST only, no updates).
    
    Args:
        add_entries: List of new entries from biotools_add.json
        config: Pipeline configuration with API settings
        token: bio.tools API token
        resume_data: Dict mapping biotools_id -> upload_status
        
    Returns:
        {
            "uploaded": int,
            "failed": int,
            "skipped": int,
            "results": List[Dict],  # detailed results per entry
        }
    """
    pass
```

## Upload Decision Logic

```python
def should_upload_entry(
    entry: Dict[str, Any],
    api_base: str,
    token: str,
) -> bool:
    """
    Decide whether to upload an entry.
    
    Returns: True if should POST, False if should skip
    """
    biotools_id = entry.get("biotoolsID")
    
    # Check if exists on bio.tools
    existing = fetch_biotools_entry(biotools_id, api_base, token)
    
    return existing is None  # Upload only if doesn't exist
```

## Error Handling Strategy

### Retry Logic
- **Transient errors (5xx)**: Retry up to 3 times with exponential backoff (1s, 2s, 4s)
- **Client errors (4xx)**: No retry, report error immediately
- **Network errors**: Retry up to 3 times

### Status Codes Handling
| Code | Meaning | Action |
|------|---------|--------|
| 201 | Created | Success, record upload_status="uploaded" |
| 400 | Bad Request | Fail, log validation error, record "failed" |
| 401 | Unauthorized | Fail entire batch, check token |
| 404 | Not Found (GET) | Entry doesn't exist, proceed with POST |
| 409 | Conflict (POST) | Entry exists, skip, record "skipped" |
| 429 | Rate Limit | Wait (exponential backoff), retry |
| 5xx | Server Error | Retry with backoff |

## Configuration Schema

```yaml
pipeline:
  # ... existing config ...
  
  upload:
    enabled: false  # Master switch (overridden by --upload flag)
    retry_attempts: 3
    retry_delay: 1.0  # Initial delay in seconds
    batch_delay: 0.5  # Delay between entries to avoid rate limits
    log_file: "upload_results.jsonl"
```

## Resume Workflow

### Initial Run
```bash
$ biotoolsllmannotate --upload --output-dir ./output
# Uploads 10 entries, 2 fail, 8 succeed
# assessment.csv records upload_status
```

### Resume After Failure
```bash
$ biotoolsllmannotate --resume-from-scoring ./output/assessment.csv --upload
# Loads CSV, sees upload_status="uploaded" for 8 entries
# Skips those 8, only retries 2 failed entries
```

### CSV State Tracking
```csv
id,name,include,upload_status
PMC123,Tool1,add,uploaded
PMC456,Tool2,add,failed
PMC789,Tool3,add,pending
```

On resume:
- `uploaded` → skip
- `failed` → retry
- `pending` → attempt upload

## Security Considerations

- **Token storage**: `.bt_token` file must have restrictive permissions (0600)
- **Token in logs**: Never log full token, use `Token: ***` redaction
- **HTTPS only**: All API calls must use HTTPS endpoints
- **Token validation**: Check token exists and is non-empty before batch upload
- **Error messages**: Don't leak token in error output

## Testing Strategy

### Unit Tests (no network)
- Mock `requests.post()` and `requests.put()`
- Test success/failure paths for each status code
- Verify retry logic with sequence of failures then success
- Check token header formatting

### Integration Tests (mock API)
- Use `responses` library to mock bio.tools API
- Test full upload orchestration with mix of new/update entries
- Verify CSV status column updates correctly
- Test resume skips uploaded entries

### Contract Tests (requires dev token)
- Actual API calls to dev server
- Mark with `@pytest.mark.biotools_dev`
- Skip in CI unless `BT_TOKEN` env var present
- Clean up test entries after run

## Backward Compatibility

- **Default behavior unchanged**: Without `--upload`, pipeline generates files as before
- **Existing configs compatible**: Upload config section is optional, defaults to disabled
- **CSV format extension**: New `upload_status` column, existing columns unchanged
- **Resume works without upload**: Can resume scoring phase without upload features

## Future Enhancements

1. **Batch upload optimization**: Group entries into single API call if API supports
2. **Dry-run mode**: `--upload-dry-run` to preview actions without POSTing
3. **Interactive mode**: Prompt for confirmation on conflicts
4. **Update capability** (future): Add PUT/PATCH support in future enhancement if needed
5. **Upload-only command**: `--upload-existing` to upload from existing JSON files without re-running pipeline
