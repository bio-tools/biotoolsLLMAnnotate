# Ollama Context Window Fix

## Problem

Ollama was truncating prompts to 4096 tokens even when using models with much larger context windows (e.g., `qwen2.5:4b` with 32K token support):

```
time=2025-11-12T07:44:07.606+01:00 level=WARN source=runner.go:125 msg="truncating input prompt" limit=4096 prompt=4654 keep=4 new=4096
```

This happened because the `num_ctx` parameter was not being set in Ollama API requests, causing Ollama to use its default of 4096 tokens.

## Solution

Added support for the `num_ctx` configuration parameter in the Ollama client:

### Code Changes

1. **Added `num_ctx` configuration reading** in `OllamaClient.__init__()`:
   - Reads `ollama.num_ctx` from config
   - Defaults to `None` (use model default)
   - Validates and converts to integer

2. **Added `num_ctx` to API payload** in `generate()`:
   - Includes `num_ctx` in the `options` field of the Ollama API request
   - Only sent when explicitly configured (not `None`)

3. **Updated trace logging** to capture `num_ctx` in trace payloads for auditing

### Configuration

Add to your `myconfig.yaml`:

```yaml
ollama:
  host: http://localhost:11434
  model: qwen2.5:4b
  num_ctx: 16384  # Set context window to 16K tokens
  max_retries: 6
  retry_backoff_seconds: 2
  concurrency: 4
```

### Recommended Values

| Model | Context Support | Recommended `num_ctx` |
|-------|----------------|----------------------|
| `qwen2.5:4b`, `qwen2.5:7b` | 32K | `16384` or `32768` |
| `llama3.2:3b` | 128K | `32768` or `65536` |
| `gemma2:9b` | 8K | `8192` |
| `mistral:7b` | 32K | `16384` |

**Note**: Higher values consume more VRAM. Monitor system resources and adjust based on available memory.

## Testing

All 84 tests passing after the fix:
- No regressions in existing functionality
- Context window now configurable per deployment
- Backward compatible (defaults to `None` = model default)

## Impact

- **Prevents prompt truncation** for models with large context windows
- **Improves scoring quality** by ensuring full prompts reach the LLM
- **Eliminates "truncating input prompt" warnings** in Ollama logs
- **Configurable per deployment** without code changes
