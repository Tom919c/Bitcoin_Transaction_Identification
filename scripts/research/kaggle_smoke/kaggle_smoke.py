"""Private Kaggle infrastructure smoke; reads no research data."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import sys
from pathlib import Path


def build_result() -> dict[str, object]:
    script_sha256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    try:
        import torch

        cuda_available = torch.cuda.is_available()
        torch_version = torch.__version__
        cuda_version = torch.version.cuda
        devices = [
            {
                "index": index,
                "name": torch.cuda.get_device_name(index),
                "total_memory_bytes": torch.cuda.get_device_properties(index).total_memory,
            }
            for index in range(torch.cuda.device_count())
        ]
        if cuda_available:
            torch.ones(1, device="cuda").add_(1).cpu()
    except Exception as error:  # Preserve diagnostics in the downloaded artifact.
        cuda_available = False
        torch_version = None
        cuda_version = None
        devices = []
        torch_error = f"{type(error).__name__}: {error}"
    else:
        torch_error = None

    return {
        "schema_version": "kaggle-infrastructure-smoke-v1",
        "status": "passed" if cuda_available else "failed",
        "purpose": "private_infrastructure_smoke_only",
        "formal_gate": False,
        "effect_metrics_read": False,
        "research_data_read": False,
        "script_sha256": script_sha256,
        "python_version": sys.version,
        "platform": platform.platform(),
        "torch_version": torch_version,
        "torch_cuda_version": cuda_version,
        "cuda_available": cuda_available,
        "cuda_devices": devices,
        "torch_error": torch_error,
    }


def main() -> int:
    result = build_result()
    output = Path(
        os.environ.get(
            "KAGGLE_SMOKE_OUTPUT", "/kaggle/working/asof_entity_graph_smoke.json"
        )
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
