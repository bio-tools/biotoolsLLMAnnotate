# Spec Delta: CLI Pipeline - Live bio.tools API Validation

## ADDED Requirements

### Requirement: Live bio.tools API Validation
The pipeline SHALL support an optional step, after scoring and registry membership checks, to validate each payload entry against the live bio.tools API.

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
