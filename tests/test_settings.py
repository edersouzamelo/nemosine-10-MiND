import ctypes
import json

import pytest

from nemosine_mind import settings


def test_local_settings_round_trip_contains_no_secret(tmp_path, monkeypatch):
    monkeypatch.setenv("MIND_DATA_DIR", str(tmp_path))

    assert settings.load_local_settings() == {}
    settings.save_local_settings("OpenAI", "gpt-5.4-mini")

    assert settings.load_local_settings() == {
        "provider": "openai",
        "model": "gpt-5.4-mini",
    }
    raw = json.loads((tmp_path / "settings.json").read_text(encoding="utf-8"))
    assert set(raw) == {"provider", "model"}


@pytest.mark.parametrize("contents", ["not-json", "[]", '{"provider":"other"}'])
def test_invalid_local_settings_are_ignored(tmp_path, monkeypatch, contents):
    monkeypatch.setenv("MIND_DATA_DIR", str(tmp_path))
    (tmp_path / "settings.json").write_text(contents, encoding="utf-8")

    assert settings.load_local_settings() == {}


def test_invalid_provider_is_not_saved(tmp_path, monkeypatch):
    monkeypatch.setenv("MIND_DATA_DIR", str(tmp_path))

    with pytest.raises(ValueError, match="Unsupported provider"):
        settings.save_local_settings("other", "model")


def test_xdg_data_directory_is_supported(tmp_path, monkeypatch):
    monkeypatch.delenv("MIND_DATA_DIR", raising=False)
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))

    assert settings.local_data_directory() == tmp_path / "mind"


def test_environment_key_takes_precedence(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "environment-secret")
    monkeypatch.setattr(
        settings,
        "read_stored_api_key",
        lambda provider: pytest.fail("vault should not be read"),
    )

    assert settings.resolve_api_key("openai") == "environment-secret"
    assert settings.provider_key_is_configured("openai") is True


def test_vault_key_is_used_when_environment_is_empty(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(
        settings, "read_stored_api_key", lambda provider: "vault-secret"
    )

    assert settings.resolve_api_key("anthropic") == "vault-secret"


def test_unavailable_vault_is_reported_as_not_configured(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(
        settings,
        "read_stored_api_key",
        lambda provider: (_ for _ in ()).throw(OSError("vault unavailable")),
    )

    assert settings.provider_key_is_configured("openai") is False


@pytest.mark.parametrize(
    ("provider", "secret"),
    [("mock", "value"), ("openai", "")],
)
def test_store_api_key_rejects_unsafe_inputs(provider, secret):
    with pytest.raises(ValueError):
        settings.store_api_key(provider, secret)


def test_store_api_key_passes_utf16_secret_to_windows_vault(monkeypatch):
    captured = {}

    class Api:
        def CredWriteW(self, pointer, flags):
            credential = pointer._obj
            captured["target"] = credential.TargetName
            captured["secret"] = ctypes.string_at(
                credential.CredentialBlob, credential.CredentialBlobSize
            ).decode("utf-16-le")
            captured["flags"] = flags
            return True

    monkeypatch.setattr(settings, "_windows_credentials_api", lambda: Api())

    settings.store_api_key("openai", "vault-value")

    assert captured == {
        "target": "MiND:openai:api-key",
        "secret": "vault-value",
        "flags": 0,
    }


def test_delete_stored_api_key_uses_provider_target(monkeypatch):
    captured = {}

    class Api:
        def CredDeleteW(self, target, credential_type, flags):
            captured.update(target=target, credential_type=credential_type, flags=flags)
            return True

    monkeypatch.setattr(settings, "_windows_credentials_api", lambda: Api())

    settings.delete_stored_api_key("anthropic")

    assert captured == {
        "target": "MiND:anthropic:api-key",
        "credential_type": 1,
        "flags": 0,
    }


def test_non_windows_vault_read_returns_none():
    if settings.os.name == "nt":
        pytest.skip("Non-Windows behavior")

    assert settings.read_stored_api_key("openai") is None
