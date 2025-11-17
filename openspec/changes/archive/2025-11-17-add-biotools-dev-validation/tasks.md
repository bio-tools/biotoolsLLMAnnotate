# Implementation Tasks

## 1. Configuration Support
- [x] 1.1 Add `biotools_api_base` field to config schema (default: `https://bio.tools/api/tool/`)
- [x] 1.2 Add `biotools_validate_api_base` field to config schema (default: `https://bio.tools/api/tool/validate/`)
- [x] 1.3 Update config loading in `main.py` to read these fields
- [x] 1.4 Add example dev server config to `myconfig.yaml` (commented out by default)

## 2. Token Management
- [x] 2.1 Create helper function `read_biotools_token()` in `biotools_api.py` to read `.bt_token` file
- [x] 2.2 Handle missing token file gracefully (return None, log info message)
- [x] 2.3 Strip whitespace from token content
- [x] 2.4 Add `.bt_token` to `.gitignore` if not already present

## 3. API Authentication
- [x] 3.1 Update `validate_biotools_entry()` signature to accept optional `token` parameter
- [x] 3.2 Add `Authorization: Token {token}` header when token is provided
- [x] 3.3 Update `fetch_biotools_entry()` to also support token authentication
- [x] 3.4 Ensure fallback to local validation on 401/403 errors

## 4. Integration
- [x] 4.1 Update `validate_biotools_payload()` in `run.py` to read token and pass API base URLs
- [x] 4.2 Update validation calls to use configured API base URL
- [x] 4.3 Add logging for which API endpoint is being used
- [x] 4.4 Add logging when token is found vs not found

## 5. Testing
- [x] 5.1 Write unit test for `read_biotools_token()` with mock file
- [x] 5.2 Write unit test for `validate_biotools_entry()` with token auth header
- [x] 5.3 Write unit test for dev server URL configuration (covered indirectly via config usage and header tests; endpoints adjustable in config)
- [x] 5.4 Write integration test with mock dev server response (tests/unit/test_biotools_api_integration.py)
- [x] 5.5 Test fallback behavior when token is missing (manual run plus unit test for local path)

## 6. Documentation
- [x] 6.1 Update `docs/BIOTOOLS_API_VALIDATION.md` with dev server setup instructions
- [x] 6.2 Document token file format and location
- [x] 6.3 Add troubleshooting section for authentication errors
- [x] 6.4 Update README with validation setup quickstart
- [x] Added temporary workaround note about homepage link suppression for dev validation
