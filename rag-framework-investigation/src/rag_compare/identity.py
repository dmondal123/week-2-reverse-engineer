"""Framework-independent, deterministic identifiers for corpus artifacts."""

import hashlib


def digest(*parts: str) -> str:
    """Return the SHA-256 hex digest of UTF-8 parts separated by U+001F."""
    return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()


def sha256_bytes(source: bytes) -> str:
    """Return the SHA-256 hex digest of source bytes."""
    return hashlib.sha256(source).hexdigest()


def document_id(source_id: str, source_bytes_sha256: str) -> str:
    """Return a stable identity for a source and its exact content."""
    return digest("document", source_id, source_bytes_sha256)


def chunk_id(document_id_value: str, start: int, end: int, text: str) -> str:
    """Return a stable identity for a document chunk and its span/text."""
    return digest("chunk", document_id_value, str(start), str(end), text)
