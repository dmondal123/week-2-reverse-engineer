"""Shared, framework-independent Ollama HTTP client.

Both adapters use this single client so embedding and generation behavior is
identical across frameworks. Calling Ollama's public REST API directly keeps
the two pipelines symmetric and avoids per-framework integration drift.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence

import requests

DEFAULT_BASE_URL = "http://127.0.0.1:11434"


class OllamaError(RuntimeError):
    """Raised when the Ollama API returns an error or an unexpected payload."""


class OllamaClient:
    """Thin client over the Ollama REST API for embeddings and generation."""

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 120.0,
        session: requests.Session | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = session or requests.Session()

    def _post(self, path: str, payload: dict) -> dict:
        try:
            response = self.session.post(
                f"{self.base_url}{path}", json=payload, timeout=self.timeout
            )
        except requests.RequestException as error:
            raise OllamaError(f"Ollama request to {path} failed: {error}") from error
        if response.status_code != 200:
            raise OllamaError(
                f"Ollama {path} returned HTTP {response.status_code}: "
                f"{response.text[:200]}"
            )
        body = response.json()
        if not isinstance(body, dict):
            raise OllamaError(f"Ollama {path} returned a non-object payload")
        return body

    def version(self) -> str:
        """Return the Ollama server version string."""
        try:
            response = self.session.get(
                f"{self.base_url}/api/version", timeout=self.timeout
            )
        except requests.RequestException as error:
            raise OllamaError(f"Ollama version check failed: {error}") from error
        if response.status_code != 200:
            raise OllamaError(f"Ollama /api/version returned {response.status_code}")
        return str(response.json().get("version", "unknown"))

    def embed(self, model: str, inputs: Sequence[str]) -> list[list[float]]:
        """Return one embedding vector per input string."""
        if not inputs:
            return []
        body = self._post("/api/embed", {"model": model, "input": list(inputs)})
        vectors = body.get("embeddings")
        if not isinstance(vectors, list) or len(vectors) != len(inputs):
            raise OllamaError("Ollama embed returned an unexpected embeddings payload")
        for vector in vectors:
            if not isinstance(vector, list) or not all(
                isinstance(value, (int, float)) for value in vector
            ):
                raise OllamaError("Ollama embed returned a non-numeric vector")
        return [list(vector) for vector in vectors]

    def generate(
        self,
        model: str,
        prompt: str,
        *,
        temperature: float = 0.0,
        top_p: float = 1.0,
        num_predict: int = 256,
        seed: int = 0,
    ) -> str:
        """Generate a single completion for the prompt with fixed options."""
        body = self._post(
            "/api/generate",
            {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "top_p": top_p,
                    "num_predict": num_predict,
                    "seed": seed,
                },
            },
        )
        text = body.get("response")
        if not isinstance(text, str):
            raise OllamaError("Ollama generate returned no response text")
        return text


def embedding_identity_digest(model: str, vectors: Sequence[Sequence[float]]) -> str:
    """Derive a deterministic identity digest for an embedding configuration.

    The digest binds the embedding namespace to the model name, the observed
    dimensionality, and a quantized probe of the first vector so that any
    change of embedding model (or dimensionality) changes release identity.
    """
    if not vectors:
        raise ValueError("at least one embedding vector is required")
    dimensions = len(vectors[0])
    probe = ",".join(f"{value:.6f}" for value in vectors[0][:32])
    payload = "\x1f".join([model, str(dimensions), probe])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
