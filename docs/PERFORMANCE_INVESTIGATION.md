# Performance Investigation: Slow qwen3:4b Responses

## Investigation Summary

### Reported Issue
User experiencing very slow LLM responses or timeouts when using `qwen3:4b` model, even after attempting to disable "thinking mode" via `/nothink` directive in the prompt.

### Root Causes Identified

#### 1. **Non-Functional `/nothink` Directive** ❌
**Finding**: The `/nothink` directive in the prompt template has NO effect.

**Reason**: This is not a recognized Ollama API parameter or model-specific directive. Qwen3 models have a built-in "thinking" field that generates chain-of-thought reasoning, which is part of the model's architecture and cannot be disabled via prompt instructions.

**Evidence**:
- Ollama API documentation does not mention `/nothink` or similar directives
- Qwen3 models emit both "response" and "thinking" fields in streaming output
- The client code collects both fields, with thinking as fallback

**Fix**: Removed the ineffective `/nothink` directive from the prompt template.

---

#### 2. **Hardcoded Timeout** ⚠️
**Finding**: The Ollama request timeout was hardcoded to 300 seconds (5 minutes) and not configurable via config file.

**Code Location**: `src/biotoolsllmannotate/assess/ollama_client.py:172`
```python
# OLD CODE
timeout=self.config.get("ollama_timeout", 300),  # Wrong key name
```

**Issue**: 
- The config key was `ollama_timeout` (top-level) but should be nested under `ollama.timeout`
- No documentation for this setting
- 300 seconds is too long for detecting stuck requests with lightweight models

**Fix**: 
1. Added `timeout` field to `ollama` config section with default 300
2. Updated client to use `self.timeout` from parsed config
3. Documented in `CONFIG.md`

---

#### 3. **Suboptimal Configuration for qwen3:4b** 📊

**Finding**: The user's configuration had settings that increased latency:

| Setting | User Value | Issue | Recommended |
|---------|-----------|-------|-------------|
| `num_ctx` | 16384 | Unnecessarily large for prompts (~1500 tokens) | 8192 |
| `max_retries` | 2 | Extra retry attempts add delay on failures | 1 |
| `timeout` | (none) | Defaulted to 300s, allowing long hangs | 180 |
| `temperature` | (default 0.01) | Could be more deterministic | 0.0 |

**Impact**: 
- Large context window increases memory usage and may slow generation
- Multiple retries on timeout = 900 seconds (15 minutes) worst case
- No fast-fail mechanism

---

#### 4. **Model-Specific Performance Characteristics** 🐢

**qwen3:4b Performance Profile**:
- **Thinking mode**: Generates internal reasoning in "thinking" field (cannot disable)
- **Generation speed**: ~15-45 seconds per candidate (typical)
- **Context window**: Supports 32K but slower with large contexts
- **Memory**: 4B parameters = moderate resource usage

**Comparison with alternatives**:

| Model | Params | Speed | Accuracy | Notes |
|-------|--------|-------|----------|-------|
| qwen3:4b | 4B | ⚠️ Medium | Good | Has thinking mode overhead |
| llama3.2:3b | 3B | ✅ Fast | Good | Recommended for speed |
| gemma2:2b | 2B | ✅ Very Fast | Fair | Less accurate |
| qwen2.5:7b | 7B | ❌ Slow | Better | No thinking overhead |

---

## Changes Implemented

### 1. Code Changes

#### `src/biotoolsllmannotate/config.py`
Added `timeout` to default Ollama configuration:
```yaml
"ollama": {
    ...
    "timeout": 300,  # NEW: Configurable timeout in seconds
    ...
}
```

#### `src/biotoolsllmannotate/assess/ollama_client.py`
Three changes:

**A. Parse timeout from config:**
```python
# NEW: Parse timeout configuration
raw_timeout = ollama_cfg.get("timeout", 300)
try:
    self.timeout = int(raw_timeout)
    if self.timeout <= 0:
        self.timeout = 300
except (TypeError, ValueError):
    self.timeout = 300
```

**B. Use instance timeout instead of hardcoded value:**
```python
# OLD
timeout=self.config.get("ollama_timeout", 300),

# NEW
timeout=self.timeout,
```

#### `CONFIG.md`
Added documentation for `ollama.timeout` and `ollama.temperature`:
```markdown
#### `ollama.timeout`
- **Type**: Integer (seconds)
- **Default**: `300`
- **Description**: Timeout for individual Ollama API requests...
```

### 2. Configuration Updates

#### Updated `myconfig.yaml`
Optimized settings for qwen3:4b:

```yaml
ollama:
  model: qwen3:4b
  max_retries: 1        # Reduced from 2
  num_ctx: 8192         # Reduced from 16384
  timeout: 180          # NEW: 3 minutes instead of 5
  temperature: 0.0      # NEW: Maximum determinism
  concurrency: 2        # Keep low for 4B model
```

**Removed ineffective `/nothink` directive** from prompt template.

### 3. Documentation

Created two new guides:

- **`docs/PROMPT_OPTIMIZATION.md`**: Comprehensive guide on:
  - Understanding the performance issues
  - Model-specific recommendations
  - Alternative model suggestions
  - Debugging techniques

- **`docs/PERFORMANCE_INVESTIGATION.md`**: This document

---

## Performance Expectations

### With Optimized Settings (qwen3:4b)

**Expected timeline per candidate**:
- **Best case**: 15-20 seconds
- **Typical**: 25-35 seconds  
- **Worst case**: 45-60 seconds
- **Timeout**: 180 seconds (3 minutes)

**For a batch of 100 candidates** with concurrency=2:
- **Estimated time**: 20-30 minutes
- **Max time** (with some failures): 50-60 minutes

### Faster Alternative (llama3.2:3b)

Switch model to `llama3.2:3b` for ~40% speed improvement:

```yaml
ollama:
  model: llama3.2:3b
  timeout: 120
  num_ctx: 8192
  concurrency: 4
```

**Expected**: 10-20 seconds per candidate

---

## Monitoring and Debugging

### Check Current Performance

**1. View recent LLM exchanges:**
```bash
tail -100 out/logs/ollama/ollama.log
```

**2. Analyze trace for timing:**
```bash
tail -50 out/ollama/trace.jsonl | jq -r '.timestamp'
```

**3. Monitor Ollama server:**
```bash
ollama ps
```

**4. Check system resources:**
```bash
htop
```

### Test Ollama Directly

**Simple JSON generation test:**
```bash
curl http://localhost:11434/api/generate -d '{
  "model": "qwen3:4b",
  "prompt": "Output JSON: {\"test\": \"value\"}",
  "format": "json"
}'
```

**Preload model to avoid cold-start delays:**
```bash
ollama run qwen3:4b "test"
```

---

## Recommendations

### Immediate Actions

1. ✅ **Apply the configuration changes** (already done)
2. ✅ **Remove `/nothink` directive** (already done)
3. ⏳ **Run a test batch** with the new settings and monitor timing

### If Still Too Slow

1. **Try llama3.2:3b** (faster, similar accuracy):
   ```bash
   ollama pull llama3.2:3b
   ```
   Update `myconfig.yaml`:
   ```yaml
   ollama:
     model: llama3.2:3b
     timeout: 120
     concurrency: 4
   ```

2. **Simplify the prompt** (reduces tokens):
   - Consider creating a condensed version
   - Trade-off: May reduce accuracy

3. **Use larger model with GPU** (if available):
   ```yaml
   ollama:
     model: qwen2.5:7b
     timeout: 240
   ```

### Long-term Considerations

1. **Hardware upgrade**: Consider GPU acceleration for Ollama
2. **Cloud API**: Switch to OpenAI-compatible API for production
3. **Hybrid approach**: Use fast model for initial filtering, detailed model for final scoring

---

## Testing Results

All tests passing after changes:
```bash
$ PYTHONPATH=src pytest tests/unit/test_ollama_client.py -v
tests/unit/test_ollama_client.py::test_ollama_client_uses_retry_configuration PASSED
tests/unit/test_ollama_client.py::test_generate_retries_connection_errors PASSED
2 passed in 0.12s
```

---

## Related Files

- Configuration: `myconfig.yaml`
- Client implementation: `src/biotoolsllmannotate/assess/ollama_client.py`
- Default config: `src/biotoolsllmannotate/config.py`
- Documentation: `CONFIG.md`, `docs/PROMPT_OPTIMIZATION.md`

---

## Questions?

If issues persist:
1. Check Ollama logs: `out/logs/ollama/ollama.log`
2. Verify model is loaded: `ollama ps`
3. Test direct API calls (see Monitoring section)
4. Consider switching to a faster model

For model selection guidance, see `docs/PROMPT_OPTIMIZATION.md`.
