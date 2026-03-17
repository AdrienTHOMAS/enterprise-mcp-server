"""Secure token storage with encrypted file backend."""

import json
import os
from pathlib import Path
from typing import Any

import structlog
from cryptography.fernet import Fernet

logger = structlog.get_logger("auth.token_store")


class TokenStore:
    """Encrypted file-based token storage.

    Stores tokens encrypted at rest using Fernet symmetric encryption.
    The encryption key can be provided directly or loaded from an
    environment variable.
    """

    def __init__(
        self,
        store_path: str = "~/.enterprise-mcp/tokens.enc",
        encryption_key: str = "",
    ) -> None:
        self._path = Path(store_path).expanduser()
        self._path.parent.mkdir(parents=True, exist_ok=True)

        key = encryption_key or os.environ.get("EMCP_TOKEN_ENCRYPTION_KEY", "")
        if not key:
            key = Fernet.generate_key().decode()
            logger.warning(
                "token_store_generated_key",
                message="No encryption key provided; generated ephemeral key. "
                "Set EMCP_TOKEN_ENCRYPTION_KEY for persistence.",
            )
        self._fernet = Fernet(key.encode() if isinstance(key, str) else key)
        self._tokens: dict[str, dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        """Load and decrypt tokens from disk."""
        if not self._path.exists():
            self._tokens = {}
            return
        try:
            encrypted = self._path.read_bytes()
            decrypted = self._fernet.decrypt(encrypted)
            self._tokens = json.loads(decrypted)
            logger.info("token_store_loaded", count=len(self._tokens))
        except Exception as exc:
            logger.error("token_store_load_failed", error=str(exc))
            self._tokens = {}

    def _save(self) -> None:
        """Encrypt and save tokens to disk."""
        raw = json.dumps(self._tokens, default=str).encode()
        encrypted = self._fernet.encrypt(raw)
        self._path.write_bytes(encrypted)

    def store_token(self, service: str, token_data: dict[str, Any]) -> None:
        """Store a token for a service."""
        self._tokens[service] = token_data
        self._save()
        logger.info("token_stored", service=service)

    def get_token(self, service: str) -> dict[str, Any] | None:
        """Retrieve a token for a service."""
        return self._tokens.get(service)

    def delete_token(self, service: str) -> bool:
        """Delete a stored token."""
        if service in self._tokens:
            del self._tokens[service]
            self._save()
            logger.info("token_deleted", service=service)
            return True
        return False

    def list_services(self) -> list[str]:
        """List all services with stored tokens."""
        return list(self._tokens.keys())
