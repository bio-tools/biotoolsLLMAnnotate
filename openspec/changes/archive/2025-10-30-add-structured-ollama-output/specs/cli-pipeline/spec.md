## ADDED Requirements
### Requirement: LLM Structured Telemetry
The pipeline scoring stage SHALL append a structured JSON line to the `logging.llm_trace` path for every Ollama `generate` attempt, defaulting to `<time_period>/ollama/trace.jsonl` when unspecified. Each record SHALL contain a unique `trace_id`, ISO-8601 UTC `timestamp`, `attempt` index, `prompt_kind` (`base` or `augmented`), the exact `prompt` text sent to Ollama, the serialized request options (`model`, `temperature`, `top_p`, `format`, `seed`), the raw concatenated `response_text`, the parsed `response_json` when available, and a `status` flag indicating `success`, `parse_error`, or `schema_error`.

The retry diagnostics exposed via `model_params` SHALL include a `trace_attempts` array mirroring the attempt order, where each element records the corresponding `trace_id`, `prompt_kind`, and any `schema_errors` captured during validation so downstream tools can join decisions with the trace log.

#### Scenario: Successful attempt recorded
- **WHEN** the first scoring attempt produces schema-valid JSON
- **THEN** the trace file gains an entry with `attempt=1`, `prompt_kind="base"`, `status="success"`, and a populated `response_json`
- **AND** `model_params.trace_attempts[0].trace_id` matches the appended entry

#### Scenario: Augmented retry captures schema failure
- **WHEN** the initial attempt fails schema validation and the scorer retries with an augmented prompt
- **THEN** the trace records the failed attempt with `status="schema_error"` alongside its validation messages and the retried attempt with `status="success"`
- **AND** `model_params.trace_attempts` lists both attempts with their trace identifiers and `prompt_kind` values
