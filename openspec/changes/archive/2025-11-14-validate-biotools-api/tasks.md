# Tasks: Validate Payload Entries Against bio.tools API


- [x] **Add configuration and CLI flag**
	- Add a config option (e.g., `validate_biotools_api: true`) and CLI flag (e.g., `--validate-biotools-api`) to enable/disable live validation after scoring.
	- Default to `false` for batch/offline safety.
- [x] **Implement bio.tools API query function**
	- Write a function to query the bio.tools API for a given tool ID and return the record or error (handle 404, network errors, etc.).
	- Support configurable API endpoint for testing.
- [x] **Integrate validation step after scoring and registry checks**
	- After scoring and registry membership checks, iterate over all payload entries.
	- For each entry, if validation is enabled, query the API and compare key fields (ID, name, status, etc.).
	- If the tool is missing or mismatched, log a warning and flag the entry in the output (e.g., add a `biotools_api_status` field).
	- Continue processing even if some API calls fail (log errors, do not abort pipeline).
- [x] **Handle API/network errors gracefully**
	- Log API/network errors and continue processing other entries.
	- Optionally collect error statistics for reporting.
- [x] **Add unit and integration tests**
	- Mock the bio.tools API for unit tests (simulate success, 404, and error cases).
	- Add integration test for the end-to-end validation step (with API mocking or test endpoint).
- [x] **Update documentation**
	- Update CLI help and configuration reference to describe the new validation step and options.
	- Document the meaning of new output fields (e.g., `biotools_api_status`).
- [x] **Create final CSV output with API status and tool details**
	- After validating all payload entries, generate a CSV file summarizing each entry.
	- Include columns for: tool ID, bio.tools API status, and key details (e.g., name, status, description, etc.).
	- Ensure the CSV is written to the run output directory and documented in CLI help.
