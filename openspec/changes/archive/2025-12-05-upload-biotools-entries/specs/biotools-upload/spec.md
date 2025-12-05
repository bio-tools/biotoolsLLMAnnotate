# Spec: bio.tools Upload

## ADDED Requirements

### Requirement: Create New Entries via API
The system SHALL POST validated bio.tools entries to the bio.tools REST API to create new tool records, handle 201 Created responses by recording upload success, reject 409 Conflict responses by logging the error and suggesting update mode, and capture 400 Bad Request validation errors in the detailed results log.

#### Scenario: Successfully create new entry
- **GIVEN** a validated entry with biotoolsID "new-tool" that doesn't exist on bio.tools
- **WHEN** the user runs with `--upload` flag
- **THEN** the system POSTs the entry to `/api/tool/`
- **AND** bio.tools returns HTTP 201 Created
- **AND** the entry upload_status is set to "uploaded" in assessment.csv

#### Scenario: Handle entry already exists conflict
- **GIVEN** a validated entry with biotoolsID "existing-tool"
- **WHEN** the system attempts to POST to create the entry
- **AND** bio.tools returns HTTP 409 Conflict
- **THEN** the system logs the conflict error
- **AND** the upload_status is set to "failed"
- **AND** the error message suggests using update mode

#### Scenario: Handle validation error from API
- **GIVEN** a validated entry that passes local validation
- **WHEN** the system POSTs to bio.tools API
- **AND** bio.tools returns HTTP 400 Bad Request with validation errors
- **THEN** the system records upload_status="failed"
- **AND** the error details are logged to upload_results.jsonl
- **AND** the console displays the validation error message

### Requirement: Check Existence Before Upload
The system SHALL query bio.tools API to check if an entry already exists before attempting to POST. If the entry exists, it SHALL skip the upload with status "skipped" and log that the entry already exists. Existing entries are not updated.

#### Scenario: Check existence and skip existing entry
- **GIVEN** an entry with biotoolsID "existing-tool"
- **AND** the tool already exists on bio.tools
- **WHEN** the user runs with `--upload` flag
- **THEN** the system fetches the entry via GET `/api/tool/existing-tool`
- **AND** receives 200 OK confirming it exists
- **AND** records upload_status="skipped"
- **AND** logs that the entry already exists

#### Scenario: Proceed with POST for new entry
- **GIVEN** an entry with biotoolsID "new-tool"
- **AND** the tool does NOT exist on bio.tools
- **WHEN** the system checks existence
- **AND** receives 404 Not Found
- **THEN** the system proceeds to POST the entry
- **AND** records result as uploaded or failed

#### Scenario: Authorization applied to existence check
- **GIVEN** a valid API token in .bt_token file
- **WHEN** the system checks if an entry exists
- **THEN** the GET request includes "Authorization: Token {token}" header
- **AND** bio.tools accepts the authenticated request

### Requirement: Token-Based Authentication
The system SHALL authenticate API requests using a token stored in .bt_token file, read the token at startup when --upload is enabled, abort with an error if the token file is missing, and halt batch uploads when receiving 401 Unauthorized responses.

#### Scenario: Load token from file
- **GIVEN** a .bt_token file exists in the repository root
- **AND** it contains a valid token string
- **WHEN** the pipeline starts with --upload
- **THEN** the system reads the token
- **AND** logs "✓ Found bio.tools authentication token"
- **AND** includes the token in all API requests

#### Scenario: Abort if token missing
- **GIVEN** no .bt_token file exists
- **WHEN** the user runs with --upload flag
- **THEN** the system prints an error message
- **AND** exits with non-zero status
- **AND** provides instructions to create .bt_token

#### Scenario: Handle unauthorized response
- **GIVEN** an invalid or expired token in .bt_token
- **WHEN** the system attempts an upload
- **AND** bio.tools returns HTTP 401 Unauthorized
- **THEN** the system aborts the batch upload
- **AND** prints a message to check token validity

### Requirement: Resume After Failure
The system SHALL track upload status in assessment.csv to enable resuming interrupted batch uploads, skip entries with upload_status="uploaded" on resume, and retry entries with status "pending" or "failed".

#### Scenario: Skip already uploaded entries on resume
- **GIVEN** a previous run uploaded 5 entries successfully
- **AND** assessment.csv records upload_status="uploaded" for those entries
- **WHEN** the user runs --resume-from-scoring with --upload
- **THEN** the system skips the 5 uploaded entries
- **AND** only attempts upload for entries with status "pending" or "failed"

#### Scenario: Retry failed entries on resume
- **GIVEN** previous run had 2 entries with upload_status="failed"
- **WHEN** resuming with --upload
- **THEN** the system retries those 2 entries
- **AND** updates their status based on new results

#### Scenario: Initial run sets pending status
- **GIVEN** first run with --upload
- **WHEN** generating assessment.csv
- **THEN** all entries have upload_status="pending" initially
- **AND** status updates to "uploaded" or "failed" after attempt

### Requirement: Error Handling and Retries
The system SHALL retry transient errors with exponential backoff, avoid retrying client errors (4xx), apply rate limit backoff for 429 responses, and configure retry attempts, initial delay, and batch delay via configuration.

#### Scenario: Retry on server error
- **GIVEN** bio.tools returns HTTP 503 Service Unavailable
- **WHEN** upload is attempted
- **THEN** the system waits 1 second and retries
- **AND** on second failure, waits 2 seconds and retries
- **AND** on third failure, waits 4 seconds and retries
- **AND** after all retries fail, records upload_status="failed"

#### Scenario: No retry on client error
- **GIVEN** bio.tools returns HTTP 400 Bad Request
- **WHEN** upload is attempted
- **THEN** the system does not retry
- **AND** immediately records upload_status="failed"
- **AND** logs the validation error details

#### Scenario: Rate limit backoff
- **GIVEN** bio.tools returns HTTP 429 Too Many Requests
- **WHEN** upload is attempted
- **THEN** the system waits for specified duration
- **AND** retries the request
- **AND** applies batch_delay between subsequent entries

### Requirement: Upload Results Reporting
The system SHALL provide clear feedback about upload outcomes via console summary displaying counts and errors, CSV upload_status column with values (uploaded, failed, skipped, pending), and detailed upload_results.jsonl log.

#### Scenario: Console summary after upload
- **GIVEN** batch upload completes
- **WHEN** pipeline finishes
- **THEN** console displays count of uploaded, failed, and skipped entries
- **AND** lists failed entries with error messages

#### Scenario: CSV status tracking
- **GIVEN** upload attempts complete
- **WHEN** assessment.csv is written
- **THEN** each row has upload_status column with appropriate value
- **AND** values are "uploaded", "failed", "skipped", or "pending"

#### Scenario: Detailed results log
- **GIVEN** upload executes
- **WHEN** entries are uploaded
- **THEN** upload_results.jsonl contains one line per entry
- **AND** includes biotoolsID, status, HTTP code, error, and timestamp

### Requirement: Configuration and Defaults
The system SHALL provide sensible defaults for upload behavior while allowing customization via config file and CLI flags, make upload opt-in (disabled by default), allow CLI flag to override config, and support retry parameter configuration.

#### Scenario: Default behavior without flag
- **GIVEN** user runs pipeline without --upload flag
- **WHEN** pipeline executes
- **THEN** payloads are generated to JSON files
- **AND** no upload is attempted
- **AND** behavior is unchanged from previous versions

#### Scenario: Override config with CLI flag
- **GIVEN** config has upload.enabled=false
- **WHEN** user specifies --upload flag
- **THEN** upload proceeds despite config setting
- **AND** CLI flag takes precedence

#### Scenario: Configure retry parameters
- **GIVEN** config specifies retry_attempts=5, retry_delay=2.0, batch_delay=1.0
- **WHEN** upload encounters retriable error
- **THEN** system retries up to 5 times
- **AND** initial delay is 2 seconds
- **AND** waits 1 second between entry uploads

### Requirement: Separation from Payload Generation
Upload SHALL be a separate optional phase that does not modify payload generation logic, allowing users to generate payloads without upload, and supporting future upload-only mode for existing payload files.

#### Scenario: Generate payloads without upload
- **GIVEN** pipeline runs without --upload
- **WHEN** payload generation completes
- **THEN** biotools_add.json and biotools_review.json are created
- **AND** no API calls are made
- **AND** assessment.csv has no upload_status column

#### Scenario: Upload uses existing payloads
- **GIVEN** biotools_add.json already exists from previous run
- **WHEN** user runs with --upload flag
- **THEN** system loads entries from JSON file
- **AND** uploads without re-running full pipeline

### Requirement: Upload Report CSV with Tool URLs
The system SHALL generate a dedicated `upload_report.csv` file after upload completes containing summary information for each upload attempt including biotoolsID, upload status, direct bio.tools URLs for successful uploads, error messages for failed uploads, HTTP status codes, and timestamps. This provides a clean actionable summary file distinct from the full assessment.csv.

#### Scenario: Generate upload report with bio.tools URLs
- **GIVEN** upload phase completes successfully
- **WHEN** entries are uploaded to bio.tools
- **AND** some uploads succeed with 201 Created
- **THEN** upload_report.csv is created in output directory
- **AND** for each successful upload, contains bio.tools API URL: `{api_base}/{biotoolsID}`
- **AND** includes columns: biotoolsID, status, bio_tools_url, error, response_code, timestamp

#### Scenario: Populate URLs only for successful uploads
- **GIVEN** upload_report.csv is being generated
- **WHEN** an entry has status="uploaded"
- **THEN** bio_tools_url is populated with `{api_base}/{biotoolsID}` (e.g., `https://bio.tools/api/tool/tool-name`)
- **AND** error column is empty

#### Scenario: Leave URL empty for failed/skipped uploads
- **GIVEN** upload_report.csv is being generated
- **WHEN** an entry has status="failed" or status="skipped"
- **THEN** bio_tools_url column is empty
- **AND** error column contains the error message (or "Entry already exists" for skipped)

#### Scenario: Report summary includes failed uploads
- **GIVEN** upload completes with some failures
- **WHEN** upload_report.csv is written
- **THEN** includes one row per attempted/skipped entry
- **AND** failed entries show HTTP status code and error details
- **AND** allows user to quickly identify which uploads need attention

## Dependencies

- Existing validation infrastructure (`validate_biotools_entry`)
- Token file support (`.bt_token`, `read_biotools_token()`)
- `requests` library for HTTP
- CSV writing in `cli/run.py` 

## Non-Requirements

- **Web UI automation**: Not using Selenium or browser automation
- **Update existing entries**: Upload only supports new entries via POST. No PUT/PATCH updates.
- **Bulk import API**: Using individual POST calls per entry
- **OAuth2 flows**: Only token-based auth supported
- **Webhook notifications**: No event-driven upload triggers
- **Edit review entries**: `biotools_review.json` entries are skipped, no uploads attempted
