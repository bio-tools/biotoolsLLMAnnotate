"""Smoke test: OpenAI-compatible mode with literal api_key from config."""
from unittest.mock import MagicMock, patch

from biotoolsllmannotate.assess.ollama_client import OllamaClient

config = {
    "ollama": {
        "host": "https://ai.cloud.sdu.dk/v1",
        "model": "zai-org/GLM-5.3-Flash",
        "api_key": "literal-token-abc",
        "max_retries": 0,
    },
    "logging": {},
}

c = OllamaClient(config=config)
assert c.openai_compatible and c.api_key == "literal-token-abc"
assert c._chat_url() == "https://ai.cloud.sdu.dk/v1/chat/completions"

fake = MagicMock()
fake.status_code = 200
fake.text = '{"choices":[{"message":{"content":"{\\"bio_score\\": 1.0}"}}]}'
fake.raise_for_status = lambda: None
with patch.object(c.session, "post", return_value=fake) as m:
    text, trace = c.generate("hello")
    assert text == '{"bio_score": 1.0}', text
    url = m.call_args[0][0]
    hdrs = m.call_args[1]["headers"]
    assert url == "https://ai.cloud.sdu.dk/v1/chat/completions"
    assert hdrs["Authorization"] == "Bearer literal-token-abc"
print("Literal api_key mode OK:", url)

# literal key must win over env var
import os

os.environ["UCLOUD_INFERENCE_TOK"] = "env-token"
c2 = OllamaClient(config=config)
assert c2.api_key == "literal-token-abc", c2.api_key
del os.environ["UCLOUD_INFERENCE_TOK"]

# native Ollama mode unaffected
c3 = OllamaClient(config={"ollama": {"host": "http://localhost:11434/"}, "logging": {}})
assert not c3.openai_compatible and c3.base_url == "http://localhost:11434"
print("Precedence + native mode OK")
