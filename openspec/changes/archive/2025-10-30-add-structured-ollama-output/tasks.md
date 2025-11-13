## 1. Implementation
- [x] 1.1 Move LLM logging defaults into an `ollama/` subfolder under each run’s `logs/` directory and update the config snapshot (both text log and new trace path)
- [x] 1.2 Add `logging.llm_trace` configuration pointing to the JSONL file and ensure the CLI scaffolds the trace file location alongside the text log
- [x] 1.3 Persist Ollama prompt/response pairs as JSONL entries from `OllamaClient`
- [x] 1.4 Enrich retry diagnostics so each attempt identifies whether the prompt was augmented and references the trace entry id
- [x] 1.5 Update docs/tests to cover the structured telemetry and folder rename
