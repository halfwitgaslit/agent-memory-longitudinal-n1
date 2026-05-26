"""Memory-backend bakeoff: 6 backends behind one ABC.

Each backend wraps a different OSS or baseline agent-memory system:

| Backend | Underlying system | Purpose |
|---|---|---|
| `mem0_backend.Mem0Backend` | mem0ai 2.0.2 + fastembed + qdrant | OSS production memory layer |
| `letta_backend.LettaBackend` | letta-client → local Letta server | Stateful agents with self-edit |
| `hindsight_backend.HindsightBackend` | hindsight-api 0.6.2 | Memory that learns (Vectorize) |
| `cognee_backend.CogneeBackend` | cognee 1.1.0 + LanceDB | Knowledge graph + vector |
| `null_backend.NullBackend` | none | Negative control |
| `random_backend.RandomBackend` | random.sample of added | Additional negative control |

All implement `MemoryBackend` ABC defined in `base.py`.
"""

from .base import Memory, MemoryBackend, BackendHealth
from .null_backend import NullBackend
from .random_backend import RandomBackend

__all__ = [
    "BackendHealth",
    "Memory",
    "MemoryBackend",
    "NullBackend",
    "RandomBackend",
]
