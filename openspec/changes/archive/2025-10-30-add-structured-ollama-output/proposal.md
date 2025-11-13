## Why
Current Ollama exchanges are appended to a human-oriented text log, which makes it painful to extract prompts, retry context, or raw JSON responses for audits and regression testing. We need a machine-readable record so downstream tooling can replay or analyze LLM behaviour.

## What Changes
- Capture every LLM request/response pair in a structured JSONL trace with timestamps, prompt variants, and normalized responses
- Expose the trace location in the CLI run configuration and ensure it is rotated along with other per-run artifacts
- Document the structured telemetry in the CLI pipeline spec so future work can rely on the JSONL format

## Impact
- Affected specs: cli-pipeline
- Affected code: `assess/ollama_client.py`, `assess/scorer.py`, `cli/run.py`, config loading
