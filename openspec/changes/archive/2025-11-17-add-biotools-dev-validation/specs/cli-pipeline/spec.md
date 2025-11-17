## MODIFIED Requirements

### Requirement: Live bio.tools API Validation
The pipeline SHALL support an optional step, after scoring and registry membership checks, to validate each payload entry against the live bio.tools API or development server. The validation endpoint SHALL be configurable via the `biotools_validate_api_base` configuration field (defaulting to `https://bio.tools/api/tool/validate/`). When a `.bt_token` file exists in the repository root, the pipeline SHALL read the token and include an `Authorization: Token {token}` header in validation requests to support authenticated dev server access. The pipeline SHALL fall back to local Pydantic validation when the token file is missing, authentication fails (401/403), or the API is unreachable.

#### Scenario: Payload entry validated against dev server with token
- **GIVEN** a `.bt_token` file exists in the repository root
- **AND** `biotools_validate_api_base` is set to `https://bio-tools-dev.sdu.dk/api/tool/validate/`
- **WHEN** validation is enabled and the pipeline validates an entry
- **THEN** the validation request includes an `Authorization: Token {token}` header
- **AND** the dev server returns validation results
- **AND** the pipeline logs successful API validation

#### Scenario: Payload entry validated against production API with token
- **GIVEN** a `.bt_token` file exists in the repository root
- **AND** `biotools_validate_api_base` is set to `https://bio.tools/api/tool/validate/` (default)
- **WHEN** validation is enabled and the pipeline validates an entry
- **THEN** the validation request includes an `Authorization: Token {token}` header
- **AND** the pipeline logs validation results

#### Scenario: Token file missing falls back to local validation
- **GIVEN** no `.bt_token` file exists
- **WHEN** validation is enabled and `use_api=True`
- **THEN** the pipeline logs that token is missing
- **AND** falls back to local Pydantic validation
- **AND** all entries are validated against the local schema

#### Scenario: Authentication failure falls back to local validation
- **GIVEN** a `.bt_token` file exists but contains an invalid token
- **WHEN** validation is enabled and the API returns 401 or 403
- **THEN** the pipeline logs the authentication error
- **AND** automatically falls back to local Pydantic validation
- **AND** the entry is validated successfully using the local schema

#### Scenario: Payload entry matches live bio.tools record
- **GIVEN** a payload entry with a valid bio.tools ID
- **WHEN** live validation is enabled
- **AND** the pipeline queries the bio.tools API for that ID
- **THEN** the API returns a matching record
- **AND** the pipeline logs successful validation

#### Scenario: Payload entry missing in live bio.tools
- **GIVEN** a payload entry with a bio.tools ID not present in the live registry
- **WHEN** live validation is enabled
- **AND** the pipeline queries the bio.tools API for that ID
- **THEN** the API returns a 404 or error
- **AND** the pipeline logs a warning and flags the entry for review

#### Scenario: API validation disabled
- **GIVEN** the validation feature is disabled by config or CLI flag
- **WHEN** the pipeline runs
- **THEN** no live API queries are made
- **AND** the pipeline proceeds as before

#### Scenario: API/network error
- **GIVEN** a network or API error occurs during validation
- **WHEN** the pipeline queries the API
- **THEN** the error is logged
- **AND** the pipeline continues processing other entries
