# Prompt Optimization Guide for Performance

## Issue: Slow LLM Responses with qwen3 Models

### Root Causes

1. **Thinking Mode**: Qwen3 models generate internal chain-of-thought reasoning in a "thinking" field, which adds significant processing time
2. **Long Prompts**: The default scoring prompt is ~1,460 tokens, which increases generation time
3. **Timeout Configuration**: The timeout wasn't configurable and defaulted to 300 seconds (5 minutes)
4. **"/nothink" Directive**: This is not a recognized Ollama or model directive - it has no effect

### Solutions Implemented

#### 1. Made Timeout Configurable
Add to your `myconfig.yaml`:
```yaml
ollama:
  timeout: 180  # Reduce from 300s to 3 minutes for faster failure detection
```

#### 2. Optimize Context Window
Qwen3:4b supports 32K tokens but Ollama defaults to 4K. Set explicitly:
```yaml
ollama:
  num_ctx: 8192  # Smaller than max (32K) but enough for our prompts
```

#### 3. Adjust Temperature
For deterministic scoring, use very low temperature:
```yaml
ollama:
  temperature: 0.0  # Maximum determinism (was 0.01)
```

### Model-Specific Recommendations

#### For qwen3:4b (Current)
```yaml
ollama:
  model: qwen3:4b
  timeout: 180          # 3 minutes
  temperature: 0.0      # Deterministic
  num_ctx: 8192        # Sufficient for prompts
  concurrency: 2       # Lower concurrency for 4B model
  max_retries: 1       # Reduce retries to fail faster
```

**Expected performance**: ~15-45 seconds per candidate

#### For Faster Models
If qwen3:4b is too slow, consider these alternatives:

1. **llama3.2:3b** (Recommended for speed)
```yaml
ollama:
  model: llama3.2:3b
  timeout: 120
  temperature: 0.0
  num_ctx: 8192
  concurrency: 4
```
**Expected performance**: ~10-20 seconds per candidate

2. **gemma2:2b** (Fastest, less accurate)
```yaml
ollama:
  model: gemma2:2b
  timeout: 60
  temperature: 0.0
  num_ctx: 8192
  concurrency: 6
```
**Expected performance**: ~5-10 seconds per candidate

3. **qwen2.5:7b** (Better accuracy, slower)
```yaml
ollama:
  model: qwen2.5:7b
  timeout: 240
  temperature: 0.0
  num_ctx: 16384
  concurrency: 1
```
**Expected performance**: ~30-90 seconds per candidate

### Prompt Optimization (Optional)

The current prompt is comprehensive but long. If you need faster responses, you can create a condensed version:

1. Remove the detailed gating checklist explanations (models can follow rules without verbose context)
2. Simplify the rubric descriptions (use bullet points instead of paragraphs)
3. Remove redundant instructions

**Warning**: Shorter prompts may reduce accuracy. Test thoroughly before deploying.

### Monitoring Performance

Check the Ollama logs to see actual generation times:
```bash
# View recent LLM exchanges
tail -100 out/logs/ollama/ollama.log

# Check trace for timing data
tail -20 out/ollama/trace.jsonl | jq -r '.timestamp'
```

### Debugging Slow Responses

If responses are still timing out:

1. **Check Ollama server load**:
   ```bash
   ollama ps
   ```

2. **Monitor system resources**:
   ```bash
   htop  # or top
   ```

3. **Test with a simple prompt**:
   ```bash
   curl http://localhost:11434/api/generate -d '{
     "model": "qwen3:4b",
     "prompt": "Output JSON: {\"test\": \"value\"}",
     "format": "json"
   }'
   ```

4. **Check model loading**:
   ```bash
   # Preload the model
   ollama run qwen3:4b "test"
   ```

### Alternative: Use OpenAI-Compatible API

If local models are too slow, consider using a cloud provider with OpenAI-compatible API:

```yaml
ollama:
  host: https://api.your-provider.com/v1
  model: gpt-4o-mini
  # Add API key via environment variable
```

Then set: `export OLLAMA_API_KEY=your-api-key`

(Note: This requires code modifications to support authentication headers)
