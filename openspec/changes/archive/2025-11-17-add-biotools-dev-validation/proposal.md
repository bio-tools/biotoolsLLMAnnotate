# Proposal: Add bio.tools Dev Server Validation

## Why
The current bio.tools validation implementation uses the production API endpoint (`https://bio.tools/api/tool/validate/`) which requires authentication and returns HTTP 401 errors. To enable schema validation during development and testing, we need to support the bio.tools development server (`bio-tools-dev.sdu.dk`) with token-based authentication stored in `.bt_token`.

## What Changes
- Add support for bio.tools dev server validation endpoint (`https://bio-tools-dev.sdu.dk/api/tool/validate/`)
- Read authentication token from `.bt_token` file in repository root
- Update `validate_biotools_entry()` to include authentication header when token is available
- Make API base URL configurable via config file or environment variable
- Add fallback to local Pydantic validation if token file is missing or API call fails
- Update documentation to explain dev server setup and token management

## Impact
- Affected specs: `cli-pipeline` (modifies existing Live bio.tools API Validation requirement)
- Affected code:
  - `src/biotoolsllmannotate/io/biotools_api.py` - Add token reading and auth header support
  - `src/biotoolsllmannotate/cli/run.py` - Pass API base URL to validation function
  - `src/biotoolsllmannotate/config.py` - Add biotools_api_base configuration option
  - `myconfig.yaml` - Example configuration for dev server
  - `docs/BIOTOOLS_API_VALIDATION.md` - Update with dev server instructions
- No breaking changes - existing behavior preserved with fallback to local validation
