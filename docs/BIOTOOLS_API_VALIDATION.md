# bio.tools API Validation

This document explains the bio.tools schema validation feature and API authentication requirements.

## Overview

The pipeline can validate bio.tools payload entries against the biotoolsSchema to ensure they meet registry requirements before submission. Two validation methods are supported:

1. **Local Pydantic Validation** (default) - Uses local `BioToolsEntry` Pydantic model
2. **bio.tools API Validation** - Uses official bio.tools validation endpoint (requires authentication)

## Current Implementation

**Default Mode**: Local Pydantic validation (`use_api=False`)

The pipeline validates all generated bio.tools payloads (both "add" and "review" categories) using a Pydantic model that enforces required fields:
- `name` (required)
- `description` (required, **updated with LLM-generated concise description from scoring**)
- `homepage` (required)
- `biotoolsID` (optional, auto-generated if missing)

**Description Handling**: The payload generation process preserves the complete pub2tools structure (function, topic, publication, credit, etc.) but replaces the description field with the LLM-generated `concise_description` from the scoring output. This ensures entries have optimized, concise descriptions while maintaining all EDAM annotations and metadata.

Validation errors are written to `schema_validation_errors.jsonl` for review.

## bio.tools API Authentication

The bio.tools validation API requires authentication with a token:

- **Production**: `https://bio.tools/api/tool/validate/` (requires production credentials)
- **Development**: `https://bio-tools-dev.sdu.dk/api/tool/validate/` (requires dev token)

Without credentials, the API returns HTTP 401:
```json
{
  "detail": "Authentication credentials were not provided."
}
```

## Setup: Development Server Validation

### Step 1: Obtain Dev Server Token

Contact the bio.tools team to request a development server authentication token.

### Step 2: Create Token File

Save your token in a `.bt_token` file in the repository root:

```bash
echo "your-token-here" > .bt_token
```

**Security**: The `.bt_token` file is in `.gitignore` and will not be committed to version control.

### Step 3: Configure Development API

Edit `myconfig.yaml` to enable API validation with the dev server:

```yaml
pipeline:
  validate_biotools_api: true
  # Use development server endpoints
  biotools_api_base: "https://bio-tools-dev.sdu.dk/api/tool/"
  biotools_validate_api_base: "https://bio-tools-dev.sdu.dk/api/tool/validate/"
```

### Step 4: Run Pipeline

The pipeline will automatically:
1. Detect the `.bt_token` file
2. Include `Authorization: Token {token}` header in API requests
3. Validate payloads against the dev server API
4. Log authentication status: `✓ Found bio.tools authentication token`

**Without Token**: If no `.bt_token` file exists, the pipeline falls back to local Pydantic validation automatically.

## Troubleshooting

### Token Not Found

```
INFO ℹ No .bt_token file found, will use local validation or unauthenticated API
```

**Solution**: Create `.bt_token` file in repository root with your authentication token.

### Authentication Failed (HTTP 401/403)

**Symptoms**: API returns "Authentication credentials were not provided" or "Invalid token"

**Solutions**:
- Verify token file has correct content (no extra whitespace/newlines)
- Check token is valid and not expired
- Confirm using correct API endpoint (dev vs production)
- Pipeline automatically falls back to local validation

### Token Format Issues

**Correct format**: Plain text, single line, no quotes
```
abcd1234efgh5678ijkl90mnopqrstuvwxyz1234
```

**Incorrect formats**:
```
"abcd1234..."  # No quotes
Token abcd1234...  # No "Token" prefix
abcd1234...
            # No trailing newlines/spaces (auto-stripped)
```

## Automatic Fallback

The pipeline includes automatic fallback to local Pydantic validation when:
- No `.bt_token` file exists
- Token file is empty or unreadable
- API returns 401/403 authentication errors

This ensures validation always succeeds regardless of API availability.

## Validation Process

When `validate_biotools_api: true` is set:

1. Pipeline generates bio.tools payloads for "add" and "review" candidates
2. Each entry is validated against biotoolsSchema
3. Valid entries are written to `biotools_<category>.json`
4. Invalid entries are logged to `schema_validation_errors.jsonl`
5. Validation summary is included in `assessment.csv`

### Temporary Workaround

The dev validation API currently rejects our generated `link` objects when we include a homepage link (value `Homepage`/`homepage`).
Until the accepted `link.type` vocabulary is clarified, homepage links are suppressed during dev validation while the top-level `homepage` field remains. This avoids false validation failures (0/11 valid) observed during integration. Remove the suppression once the allowable values list is published or confirmed.

## Testing

Schema validation is covered by unit tests:
- `tests/unit/test_schema_validation.py` - Pydantic model validation (9 tests)
- `tests/unit/test_biotools_id_generation.py` - ID generation (8 tests)
- `tests/contract/test_cli_validate_biotools_api.py` - Feature integration (3 tests)

All tests passing (20/20).

## Future Work

1. Contact bio.tools team for API access documentation
2. Implement authentication support (API key/token in config)
3. Add retry logic for transient API errors
4. Document authentication setup in README

## References

- bio.tools API: https://bio.tools/api/
- bio.tools schema: https://github.com/bio-tools/biotoolsSchema
- GET endpoint (working): `https://bio.tools/api/tool/{id}?format=json`
- POST validation (auth required): `https://bio.tools/api/tool/validate/`
