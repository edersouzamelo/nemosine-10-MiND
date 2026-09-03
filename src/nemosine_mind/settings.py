"""Local provider settings and secret storage for the installed MiND app."""

from __future__ import annotations

import ctypes
import json
import os
from ctypes import wintypes
from pathlib import Path
from typing import Any, Dict, Optional

SUPPORTED_PROVIDERS = {"mock", "openai", "anthropic"}
DEFAULT_MODELS = {
    "mock": "mind-mock-1",
    "openai": "gpt-5.4-mini",
    "anthropic": "",
}
_CREDENTIAL_TYPE_GENERIC = 1
_CREDENTIAL_PERSIST_LOCAL_MACHINE = 2
_ERROR_NOT_FOUND = 1168


def _ctypes_member(name: str) -> Any:
    """Access Windows-only ctypes members without breaking checks on other OSes."""
    return getattr(ctypes, name)


def local_data_directory() -> Path:
    """Return a per-user writable directory shared by settings and runtime data."""
    configured = os.getenv("MIND_DATA_DIR")
    if configured:
        return Path(configured).expanduser()
    if os.name == "nt" and os.getenv("LOCALAPPDATA"):
        return Path(os.environ["LOCALAPPDATA"]) / "MiND"
    xdg_data_home = os.getenv("XDG_DATA_HOME")
    if xdg_data_home:
        return Path(xdg_data_home).expanduser() / "mind"
    return Path.home() / ".local" / "share" / "mind"


def settings_path() -> Path:
    return local_data_directory() / "settings.json"


def load_local_settings() -> Dict[str, str]:
    """Load only the non-secret provider preferences that MiND understands."""
    path = settings_path()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, ValueError, TypeError):
        return {}
    if not isinstance(raw, dict):
        return {}
    provider = str(raw.get("provider", "")).strip().lower()
    model = str(raw.get("model", "")).strip()
    if provider not in SUPPORTED_PROVIDERS:
        return {}
    return {"provider": provider, "model": model}


def save_local_settings(provider: str, model: str) -> None:
    """Atomically persist provider preferences without ever including API keys."""
    normalized = provider.strip().lower()
    if normalized not in SUPPORTED_PROVIDERS:
        raise ValueError("Unsupported provider")
    path = settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(
        json.dumps({"provider": normalized, "model": model.strip()}, indent=2),
        encoding="utf-8",
    )
    temporary.replace(path)


class _FILETIME(ctypes.Structure):
    _fields_ = [("dwLowDateTime", wintypes.DWORD), ("dwHighDateTime", wintypes.DWORD)]


class _CREDENTIALW(ctypes.Structure):
    _fields_ = [
        ("Flags", wintypes.DWORD),
        ("Type", wintypes.DWORD),
        ("TargetName", wintypes.LPWSTR),
        ("Comment", wintypes.LPWSTR),
        ("LastWritten", _FILETIME),
        ("CredentialBlobSize", wintypes.DWORD),
        ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)),
        ("Persist", wintypes.DWORD),
        ("AttributeCount", wintypes.DWORD),
        ("Attributes", ctypes.c_void_p),
        ("TargetAlias", wintypes.LPWSTR),
        ("UserName", wintypes.LPWSTR),
    ]


_PCREDENTIALW = ctypes.POINTER(_CREDENTIALW)


def _credential_target(provider: str) -> str:
    return f"MiND:{provider.strip().lower()}:api-key"


def _windows_credentials_api() -> Any:
    if os.name != "nt":
        raise OSError("Windows Credential Manager is unavailable")
    win_dll = _ctypes_member("WinDLL")
    api = win_dll("Advapi32.dll", use_last_error=True)
    api.CredWriteW.argtypes = [ctypes.POINTER(_CREDENTIALW), wintypes.DWORD]
    api.CredWriteW.restype = wintypes.BOOL
    api.CredReadW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.POINTER(_PCREDENTIALW),
    ]
    api.CredReadW.restype = wintypes.BOOL
    api.CredDeleteW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
    ]
    api.CredDeleteW.restype = wintypes.BOOL
    api.CredFree.argtypes = [ctypes.c_void_p]
    api.CredFree.restype = None
    return api


def store_api_key(provider: str, secret: str) -> None:
    """Store a provider key in the current user's Windows Credential Manager."""
    normalized = provider.strip().lower()
    value = secret.strip()
    if normalized not in {"openai", "anthropic"}:
        raise ValueError("API keys are supported only for commercial providers")
    if not value:
        raise ValueError("API key cannot be empty")
    api = _windows_credentials_api()
    encoded = value.encode("utf-16-le")
    blob = (ctypes.c_ubyte * len(encoded)).from_buffer_copy(encoded)
    credential = _CREDENTIALW()
    credential.Type = _CREDENTIAL_TYPE_GENERIC
    credential.TargetName = _credential_target(normalized)
    credential.CredentialBlobSize = len(encoded)
    credential.CredentialBlob = ctypes.cast(blob, ctypes.POINTER(ctypes.c_ubyte))
    credential.Persist = _CREDENTIAL_PERSIST_LOCAL_MACHINE
    credential.UserName = "MiND local user"
    if not api.CredWriteW(ctypes.byref(credential), 0):
        error = _ctypes_member("get_last_error")()
        raise OSError(error, "Windows Credential Manager rejected the key")


def read_stored_api_key(provider: str) -> Optional[str]:
    """Read a provider key without exposing it through a public API response."""
    if os.name != "nt":
        return None
    api = _windows_credentials_api()
    pointer = _PCREDENTIALW()
    if not api.CredReadW(
        _credential_target(provider), _CREDENTIAL_TYPE_GENERIC, 0, ctypes.byref(pointer)
    ):
        error = _ctypes_member("get_last_error")()
        if error == _ERROR_NOT_FOUND:
            return None
        raise OSError(error, "Windows Credential Manager could not read the key")
    try:
        credential = pointer.contents
        raw = ctypes.string_at(credential.CredentialBlob, credential.CredentialBlobSize)
        return raw.decode("utf-16-le")
    finally:
        api.CredFree(pointer)


def delete_stored_api_key(provider: str) -> None:
    """Remove a provider key from Windows Credential Manager if it exists."""
    api = _windows_credentials_api()
    if api.CredDeleteW(_credential_target(provider), _CREDENTIAL_TYPE_GENERIC, 0):
        return
    error = _ctypes_member("get_last_error")()
    if error != _ERROR_NOT_FOUND:
        raise OSError(error, "Windows Credential Manager could not delete the key")


def resolve_api_key(provider: str) -> str:
    """Prefer an explicit process environment variable, then the Windows vault."""
    normalized = provider.strip().lower()
    env_name = f"{normalized.upper()}_API_KEY"
    environment_value = os.getenv(env_name, "").strip()
    if environment_value:
        return environment_value
    return read_stored_api_key(normalized) or ""


def provider_key_is_configured(provider: str) -> bool:
    try:
        return bool(resolve_api_key(provider))
    except OSError:
        return False
