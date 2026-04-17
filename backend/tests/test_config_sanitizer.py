import pytest

from app.services.config_sanitizer import strip_secrets


def test_strips_top_level_named_secrets():
    cfg = {
        "anthropic_api_key": "sk-ant-x", "openai_api_key": "sk-x", "google_api_key": "g",
        "mistral_api_key": "m", "ollama_base_url": "http://localhost:11434",
        "analyst_model": "claude-3-5-sonnet-20241022", "temperature": 0.7,
    }
    out = strip_secrets(cfg)
    assert "anthropic_api_key" not in out
    assert "openai_api_key" not in out
    assert "google_api_key" not in out
    assert "mistral_api_key" not in out
    assert "ollama_base_url" not in out
    assert out["analyst_model"] == "claude-3-5-sonnet-20241022"
    assert out["temperature"] == 0.7


def test_strips_nested_secrets_in_custom_endpoints():
    cfg = {
        "custom_endpoints": [
            {"id": "e1", "name": "x", "base_url": "https://x", "api_key": "secret", "models": []},
            {"id": "e2", "api_key": "another", "name": "y"},
        ],
    }
    out = strip_secrets(cfg)
    assert out["custom_endpoints"][0]["base_url"] == "https://x"
    assert "api_key" not in out["custom_endpoints"][0]
    assert "api_key" not in out["custom_endpoints"][1]


@pytest.mark.parametrize("key", ["foo_api_key", "fooApiKey", "fooSecret", "auth_token", "user_password"])
def test_strips_keys_matching_secret_pattern(key):
    cfg = {"keep": 1, key: "very-secret"}
    out = strip_secrets(cfg)
    assert key not in out
    assert out["keep"] == 1


def test_does_not_strip_unrelated_keys():
    cfg = {"window_size": 50, "temperature": 0.5, "session_strategy": "truncate"}
    assert strip_secrets(cfg) == cfg
