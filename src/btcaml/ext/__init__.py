"""Sprint-1 extension models (additive only; no existing files modified).

New models for the pre-registered sprint-1 campaign:
- ``DirSAGE``: direction-separated GraphSAGE baseline without edge features/gates.
- ``DGResEGS``: EGS backbone + node-only self branch (+ optional scalar gate),
  composed here so the frozen EGS implementation stays untouched.
"""

from __future__ import annotations

from .dir_sage import DirSAGE
from .dg_resegs import DGResEGS

__all__ = ["DirSAGE", "DGResEGS"]
