from __future__ import annotations

import hashlib
import math
import struct
from abc import ABC, abstractmethod


EMBEDDING_DIM = 1024


class EmbeddingClient(ABC):
    dim: int = EMBEDDING_DIM

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError


class HashEmbeddingClient(EmbeddingClient):
    """Deterministic local stub for tests / offline dev (not for production quality)."""

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [_hash_vector(t, self.dim) for t in texts]


def _hash_vector(text: str, dim: int) -> list[float]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    # Expand digest into dim floats in [-1, 1], then L2-normalize
    vals: list[float] = []
    seed = digest
    while len(vals) < dim:
        seed = hashlib.sha256(seed).digest()
        for i in range(0, len(seed) - 3, 4):
            if len(vals) >= dim:
                break
            n = struct.unpack_from(">I", seed, i)[0]
            vals.append((n / 0xFFFFFFFF) * 2.0 - 1.0)
    norm = math.sqrt(sum(v * v for v in vals)) or 1.0
    return [v / norm for v in vals]
