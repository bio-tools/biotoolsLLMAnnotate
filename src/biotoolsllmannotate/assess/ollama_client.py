import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from biotoolsllmannotate.config import get_config_yaml


class OllamaConnectionError(Exception):
    """Raised when Ollama service is unavailable."""

    pass


class OllamaGenerationError(ValueError):
    """Raised when the LLM response cannot be parsed into JSON."""

    def __init__(self, message: str, trace_payload: dict[str, Any]):
        super().__init__(message)
        self.trace_payload = trace_payload


class OllamaClient:
    """Wrapper for interacting with local Ollama LLM server with connection pooling and retries."""

    def __init__(self, base_url=None, config=None):
        self.config = config or get_config_yaml()
        ollama_cfg = self.config.get("ollama", {}) or {}
        self.base_url = base_url or ollama_cfg.get("host", "http://localhost:11434")
        logging_cfg = self.config.get("logging", {}) or {}
        log_path = logging_cfg.get("llm_log")
        trace_path = logging_cfg.get("llm_trace")
        self.llm_log_path = (
            Path(log_path) if log_path else Path("out/logs/ollama/ollama.log")
        )
        self.llm_trace_path = (
            Path(trace_path) if trace_path else Path("out/ollama/trace.jsonl")
        )
        raw_force_json = ollama_cfg.get("force_json_format", True)
        if isinstance(raw_force_json, str):
            self.force_json_format = raw_force_json.strip().lower() not in {
                "0",
                "false",
                "no",
                "off",
            }
        else:
            self.force_json_format = bool(raw_force_json)

        raw_retries = ollama_cfg.get("max_retries", self.config.get("max_attempts", 3))
        try:
            parsed_retries = int(raw_retries)
        except (TypeError, ValueError):
            parsed_retries = 3
        self.max_retries = max(0, parsed_retries)

        raw_backoff = ollama_cfg.get(
            "retry_backoff_seconds",
            self.config.get("backoff_seconds", 2),
        )
        try:
            self.retry_backoff_seconds = float(raw_backoff)
        except (TypeError, ValueError):
            self.retry_backoff_seconds = 2.0
        if self.retry_backoff_seconds < 0:
            self.retry_backoff_seconds = 0.0

        raw_temperature = ollama_cfg.get("temperature", 0.01)
        try:
            self.temperature = float(raw_temperature)
        except (TypeError, ValueError):
            self.temperature = 0.01
        if self.temperature < 0:
            self.temperature = 0.0

        raw_top_p = ollama_cfg.get("top_p", 1.0)
        try:
            self.top_p = float(raw_top_p)
        except (TypeError, ValueError):
            self.top_p = 1.0
        if self.top_p <= 0:
            self.top_p = 1.0

        # Timeout for Ollama API requests (in seconds)
        raw_timeout = ollama_cfg.get("timeout", 300)
        try:
            self.timeout = int(raw_timeout)
            if self.timeout <= 0:
                self.timeout = 300
        except (TypeError, ValueError):
            self.timeout = 300

        # Context window size (num_ctx parameter for Ollama)
        # Default to None to use the model's default; set explicitly to override
        raw_num_ctx = ollama_cfg.get("num_ctx")
        if raw_num_ctx is not None:
            try:
                self.num_ctx = int(raw_num_ctx)
                if self.num_ctx <= 0:
                    self.num_ctx = None
            except (TypeError, ValueError):
                self.num_ctx = None
        else:
            self.num_ctx = None

        # Setup session with connection pooling and retries
        self.session = requests.Session()
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=self.retry_backoff_seconds,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(
            max_retries=retry_strategy, pool_connections=10, pool_maxsize=20
        )
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.session.headers.update({"Connection": "keep-alive"})

    def generate(
        self,
        prompt,
        model=None,
        temperature=None,
        top_p=None,
        seed=None,
        trace_context: Optional[dict[str, Any]] = None,
    ) -> tuple[str, dict[str, Any]]:
        from tenacity import retry, stop_after_attempt, wait_fixed

        max_attempts = max(1, 1 + self.max_retries)
        backoff = self.retry_backoff_seconds

        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_fixed(backoff),
            reraise=True,
        )
        def _call():
            resolved_temperature = (
                self.temperature if temperature is None else temperature
            )
            try:
                resolved_temperature = float(resolved_temperature)
            except (TypeError, ValueError):
                resolved_temperature = self.temperature
            if resolved_temperature < 0:
                resolved_temperature = 0.0

            resolved_top_p = self.top_p if top_p is None else top_p
            try:
                resolved_top_p = float(resolved_top_p)
            except (TypeError, ValueError):
                resolved_top_p = self.top_p
            if resolved_top_p <= 0:
                resolved_top_p = self.top_p

            payload = {
                "model": model or self.config.get("ollama", {}).get("model"),
                "prompt": prompt,
                "temperature": resolved_temperature,
                "top_p": resolved_top_p,
            }
            if self.force_json_format:
                payload["format"] = "json"
            if seed is not None:
                payload["seed"] = seed
            if self.num_ctx is not None:
                payload["options"] = payload.get("options", {})
                payload["options"]["num_ctx"] = self.num_ctx
            trace_payload = self._build_trace_payload(prompt, payload, trace_context)
            try:
                resp = self.session.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=self.timeout,
                )
                resp.raise_for_status()
            except requests.exceptions.HTTPError as e:
                if resp.status_code == 404 and "not found" in resp.text:
                    model_name = payload.get("model", "unknown")
                    raise OllamaConnectionError(
                        f"Model '{model_name}' not found in Ollama. Available models: ollama list"
                    ) from e
                raise OllamaConnectionError(f"Ollama HTTP error: {e}") from e
            except requests.exceptions.RequestException as e:
                raise OllamaConnectionError(
                    f"Failed to connect to Ollama at {self.base_url}: {e}"
                ) from e
            combined = ""
            thinking_text = ""
            for line in resp.text.strip().splitlines():
                try:
                    obj = json.loads(line)
                    if isinstance(obj, dict):
                        # Collect response field (the actual output)
                        if "response" in obj and obj["response"]:
                            combined += obj["response"]
                        # Collect thinking field separately (chain-of-thought reasoning)
                        # Some models like qwen3 use this for intermediate reasoning
                        if "thinking" in obj and obj["thinking"]:
                            thinking_text += obj["thinking"]
                except Exception:
                    continue

            # Prefer actual response; fall back to thinking if no response was generated
            # This handles models that only emit thinking without a final response field
            final_output = combined if combined else thinking_text
            trace_payload["response_text"] = final_output or resp.text

            def _attempt_parse(text: str) -> str | None:
                start = text.find("{")
                end = text.rfind("}")
                if start == -1 or end == -1 or end <= start:
                    return None
                candidate = text[start : end + 1]
                try:
                    json.loads(candidate)
                    return candidate
                except json.JSONDecodeError:
                    return None

            final_json = _attempt_parse(final_output)
            if final_json is None:
                final_json = _attempt_parse(resp.text)

            if final_json is not None:
                self._log_exchange(payload, final_json, is_json=True)
                trace_payload["response_json_text"] = final_json
                return final_json, trace_payload

            self._log_exchange(payload, final_output, is_json=False)
            raise OllamaGenerationError(
                "No valid JSON object found in Ollama response",
                trace_payload,
            )

        return _call()

    def ping(self) -> tuple[bool, Optional[str]]:
        """Check whether the Ollama endpoint is reachable."""
        try:
            resp = self.session.get(f"{self.base_url}/api/tags", timeout=10)
            resp.raise_for_status()
            return True, None
        except requests.exceptions.ConnectionError:
            return (
                False,
                f"Connection failed: Ollama service not available at {self.base_url}",
            )
        except requests.exceptions.Timeout:
            return (
                False,
                f"Timeout: Ollama service at {self.base_url} took too long to respond",
            )
        except requests.exceptions.RequestException as exc:
            return False, f"Request failed: {exc}"
        except Exception as exc:
            return False, f"Unexpected error: {exc}"

    def _log_exchange(self, payload, response_text, *, is_json: bool):
        try:
            self.llm_log_path.parent.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now(UTC).isoformat()
            with self.llm_log_path.open("a", encoding="utf-8") as f:
                f.write("==== BEGIN OLLAMA REQUEST\n")
                f.write(f"timestamp: {timestamp}\n")
                f.write(json.dumps(payload, ensure_ascii=False, indent=2))
                f.write("\n---- RESPONSE\n")
                if is_json:
                    try:
                        parsed = json.loads(response_text)
                        pretty = json.dumps(parsed, ensure_ascii=False, indent=2)
                    except Exception:
                        pretty = response_text
                else:
                    pretty = response_text
                if not pretty.endswith("\n"):
                    pretty += "\n"
                f.write(pretty)
                f.write("==== END OLLAMA REQUEST\n\n")
        except Exception:
            pass

    def _build_trace_payload(
        self,
        prompt: str,
        payload: dict[str, Any],
        trace_context: Optional[dict[str, Any]],
    ) -> dict[str, Any]:
        context = trace_context or {}
        options: dict[str, Any] = {}
        for key in ("model", "temperature", "top_p", "format", "seed"):
            if key in payload and payload[key] is not None:
                options[key] = payload[key]
        # Include nested options like num_ctx
        if "options" in payload and isinstance(payload["options"], dict):
            options["options"] = payload["options"]
        return {
            "trace_id": uuid4().hex,
            "prompt": prompt,
            "options": options,
            "attempt": context.get("attempt"),
            "prompt_kind": context.get("prompt_kind", "base"),
            "response_text": "",
        }

    def write_trace_entry(
        self,
        trace_payload: Optional[dict[str, Any]],
        *,
        status: str,
        response_json: Any | None,
        schema_errors: Optional[list[str]] = None,
    ) -> None:
        if not trace_payload:
            return
        entry: dict[str, Any] = {
            "trace_id": trace_payload.get("trace_id"),
            "timestamp": datetime.now(UTC).isoformat(),
            "attempt": trace_payload.get("attempt"),
            "prompt_kind": trace_payload.get("prompt_kind"),
            "prompt": trace_payload.get("prompt", ""),
            "request_options": trace_payload.get("options", {}),
            "response_text": trace_payload.get("response_text", ""),
            "status": status,
        }
        if response_json is not None:
            entry["response_json"] = response_json
        if schema_errors:
            entry["schema_errors"] = schema_errors
        try:
            self.llm_trace_path.parent.mkdir(parents=True, exist_ok=True)
            with self.llm_trace_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, ensure_ascii=False))
                fh.write("\n")
        except Exception:
            pass
