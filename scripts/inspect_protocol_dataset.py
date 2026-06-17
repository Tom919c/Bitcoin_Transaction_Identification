#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Inspect a PyG protocol dataset (.pt) produced by build_protocol_dataset.py.

Usage:
  python scripts/inspect_protocol_dataset.py --path data/processed/protocols/class_balanced_khop.pt
  python scripts/inspect_protocol_dataset.py --data-dir data/processed/protocols
"""

from __future__ import annotations

import argparse
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import torch

import _bootstrap  # noqa: F401
from btcaml.utils.run_artifacts import RunArtifacts


DEFAULT_LABEL_NAMES_11 = {
    -1: "UNLABELED",
    0: "INDIVIDUAL",
    1: "BET",
    2: "GAMBLING",
    3: "EXCHANGE",
    4: "MINING",
    5: "PONZI",
    6: "RANSOMWARE",
    7: "FAUCET",
    8: "MARKETPLACE",
    9: "MIXER",
    10: "BRIDGE",
}

def load_pt(path: Path) -> Any:
    try:
        return torch.load(path, map_location="cpu", weights_only=False)
    except TypeError:
        return torch.load(path, map_location="cpu")


def get_data(obj: Any) -> Any:
    # Common save formats: Data directly, {"data": Data}, {"dataset": Data}
    if isinstance(obj, dict):
        for key in ("data", "dataset", "graph"):
            if key in obj:
                return obj[key]
    return obj


def get_metadata(obj: Any) -> Dict[str, Any]:
    if isinstance(obj, dict):
        meta = obj.get("metadata") or obj.get("meta") or {}
        if isinstance(meta, dict):
            return meta
    return {}


def has_attr(data: Any, name: str) -> bool:
    try:
        return hasattr(data, name) and getattr(data, name) is not None
    except Exception:
        return False


def get_attr(data: Any, name: str, default: Any = None) -> Any:
    try:
        return getattr(data, name) if hasattr(data, name) else default
    except Exception:
        return default


def tensor_shape(x: Any) -> str:
    if torch.is_tensor(x):
        return "x".join(str(v) for v in tuple(x.shape))
    return "-"


def nan_min(x: torch.Tensor) -> float:
    x = x.float()
    x = x[torch.isfinite(x)]
    return float(x.min().item()) if x.numel() else float("nan")


def nan_max(x: torch.Tensor) -> float:
    x = x.float()
    x = x[torch.isfinite(x)]
    return float(x.max().item()) if x.numel() else float("nan")


def nan_mean(x: torch.Tensor) -> float:
    x = x.float()
    x = x[torch.isfinite(x)]
    return float(x.mean().item()) if x.numel() else float("nan")


def finite_values(x: torch.Tensor) -> torch.Tensor:
    x = x.float().flatten()
    return x[torch.isfinite(x)]


def percentile(x: torch.Tensor, q: float) -> float:
    x = finite_values(x)
    if x.numel() == 0:
        return float("nan")
    values = torch.sort(x).values
    pos = int(round((values.numel() - 1) * q))
    pos = max(0, min(pos, values.numel() - 1))
    return float(values[pos].item())


def time_stats_row(name: str, values: torch.Tensor) -> List[Any]:
    values = finite_values(values)
    return [
        name,
        int(values.numel()),
        f"{nan_min(values):.2f}",
        f"{percentile(values, 0.25):.2f}",
        f"{percentile(values, 0.50):.2f}",
        f"{nan_mean(values):.2f}",
        f"{percentile(values, 0.75):.2f}",
        f"{nan_max(values):.2f}",
    ]


def supervised_mask(y: torch.Tensor) -> torch.Tensor:
    # Current protocol datasets use -1 for unlabeled and 0..10 for supervised classes.
    return y >= 0


def safe_num_nodes(data: Any) -> int:
    n = get_attr(data, "num_nodes", None)
    if n is not None:
        return int(n)
    x = get_attr(data, "x", None)
    if torch.is_tensor(x):
        return int(x.size(0))
    y = get_attr(data, "y", None)
    if torch.is_tensor(y):
        return int(y.numel())
    return -1


def safe_num_edges(data: Any) -> int:
    edge_index = get_attr(data, "edge_index", None)
    if torch.is_tensor(edge_index) and edge_index.dim() == 2:
        return int(edge_index.size(1))
    return -1


def infer_label_names(obj: Any, data: Any) -> Dict[int, str]:
    # Try metadata first, then fallback.
    candidates: List[Any] = []
    if isinstance(obj, dict):
        for key in ("label_names", "id_to_label", "label_map", "metadata", "meta"):
            if key in obj:
                candidates.append(obj[key])
    for key in ("label_names", "id_to_label", "label_map", "metadata", "meta"):
        v = get_attr(data, key, None)
        if v is not None:
            candidates.append(v)

    for cand in candidates:
        if isinstance(cand, dict):
            # id -> name
            if all(str(k).lstrip("-").isdigit() for k in cand.keys()):
                return {int(k): str(v) for k, v in cand.items()}
            # name -> id
            if all(str(v).lstrip("-").isdigit() for v in cand.values()):
                return {int(v): str(k) for k, v in cand.items()}
            # nested metadata
            for key in ("label_names", "id_to_label", "label_map"):
                nested = cand.get(key)
                if isinstance(nested, dict):
                    if all(str(k).lstrip("-").isdigit() for k in nested.keys()):
                        return {int(k): str(v) for k, v in nested.items()}
                    if all(str(v).lstrip("-").isdigit() for v in nested.values()):
                        return {int(v): str(k) for k, v in nested.items()}
            label_space = str(cand.get("label_space", ""))
            if label_space == "11":
                return DEFAULT_LABEL_NAMES_11.copy()

    return DEFAULT_LABEL_NAMES_11.copy()


def print_table(rows: List[List[Any]], headers: List[str]) -> None:
    if not rows:
        print("(empty)")
        return
    widths = [len(str(h)) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))
    fmt = " | ".join("{:<" + str(w) + "}" for w in widths)
    sep = "-+-".join("-" * w for w in widths)
    print(fmt.format(*headers))
    print(sep)
    for row in rows:
        print(fmt.format(*row))


def class_counts(y: torch.Tensor, mask: Optional[torch.Tensor], label_names: Dict[int, str]) -> List[List[Any]]:
    if mask is not None:
        y = y[mask.bool()]
    if y.numel() == 0:
        return []
    labels, counts = torch.unique(y.cpu(), return_counts=True)
    rows: List[List[Any]] = []
    for label, count in zip(labels.tolist(), counts.tolist()):
        rows.append([int(label), label_names.get(int(label), str(int(label))), int(count)])
    return rows


def mask_summary(data: Any, y: Optional[torch.Tensor], label_names: Dict[int, str]) -> None:
    masks = []
    for name in ("train_mask", "val_mask", "test_mask"):
        m = get_attr(data, name, None)
        if torch.is_tensor(m):
            masks.append((name, m.bool()))

    print("\n## Split masks")
    if not masks:
        print("No train_mask / val_mask / test_mask found.")
        return

    rows = []
    for name, mask in masks:
        rows.append([name, int(mask.sum().item()), f"{float(mask.float().mean().item()) * 100:.4f}%"])
    print_table(rows, ["mask", "count", "node_ratio"])

    overlap_rows = []
    for i in range(len(masks)):
        for j in range(i + 1, len(masks)):
            overlap = int((masks[i][1] & masks[j][1]).sum().item())
            overlap_rows.append([masks[i][0], masks[j][0], overlap])
    print("\n## Split overlaps")
    print_table(overlap_rows, ["mask_a", "mask_b", "overlap"])

    union = torch.zeros_like(masks[0][1], dtype=torch.bool)
    for _, mask in masks:
        union |= mask
    print(f"\nSplit union count: {int(union.sum().item())}")

    if y is not None and torch.is_tensor(y):
        labeled = supervised_mask(y)
        labeled_in_split = int((union & labeled).sum().item())
        labeled_total = int(labeled.sum().item())
        print(f"Labeled covered by split masks: {labeled_in_split}/{labeled_total}")

        for name, mask in masks:
            print(f"\n## Class distribution: {name}")
            rows = class_counts(y, mask & labeled, label_names)
            print_table(rows, ["id", "label", "count"])


def split_masks(data: Any) -> List[Tuple[str, torch.Tensor]]:
    masks = []
    for name in ("train_mask", "val_mask", "test_mask"):
        m = get_attr(data, name, None)
        if torch.is_tensor(m):
            masks.append((name.replace("_mask", ""), m.bool()))
    return masks


def temporal_summary(
    data: Any,
    metadata: Optional[Dict[str, Any]] = None,
    y: Optional[torch.Tensor] = None,
    label_names: Optional[Dict[int, str]] = None,
) -> None:
    metadata = metadata or {}
    label_names = label_names or {}
    print("\n## Temporal fields")
    candidates = [
        "time", "node_time", "timestamp", "block_height",
        "first_transaction_in", "last_transaction_in",
        "first_transaction_out", "last_transaction_out",
        "first_seen", "last_seen",
    ]
    found = False
    for name in candidates:
        v = get_attr(data, name, None)
        if torch.is_tensor(v) and v.numel() > 0:
            found = True
            vv = v.float()
            print(
                f"{name}: shape={tensor_shape(v)}, "
                f"min={nan_min(vv):.2f}, "
                f"max={nan_max(vv):.2f}, "
                f"mean={nan_mean(vv):.2f}"
            )
    if not found:
        print("No obvious node-level temporal tensor found.")

    node_time = get_attr(data, "node_time", None)
    if torch.is_tensor(node_time) and node_time.numel() > 0 and torch.is_tensor(y):
        labeled = supervised_mask(y)
        masks = split_masks(data)
        if masks:
            print("\n## Split temporal summary (supervised nodes)")
            rows = []
            for name, mask in masks:
                rows.append(time_stats_row(name, node_time[mask & labeled]))
            print_table(
                rows,
                ["split", "count", "time_min", "time_p25", "time_median", "time_mean", "time_p75", "time_max"],
            )

            print("\n## Per-class split temporal summary")
            class_rows = []
            for label_id in sorted(int(x) for x in torch.unique(y[labeled]).tolist()):
                label_mask = y == label_id
                for split_name, split_mask in masks:
                    values = node_time[split_mask & label_mask]
                    if values.numel() == 0:
                        continue
                    class_rows.append([
                        label_names.get(label_id, str(label_id)),
                        split_name,
                        int(values.numel()),
                        f"{nan_min(values):.2f}",
                        f"{percentile(values, 0.50):.2f}",
                        f"{nan_max(values):.2f}",
                    ])
            print_table(class_rows, ["label", "split", "count", "time_min", "time_median", "time_max"])

    edge_attr = get_attr(data, "edge_attr", None)
    edge_feature_names = (
        get_attr(data, "edge_feature_names", None)
        or metadata.get("edge_feature_columns")
    )
    if torch.is_tensor(edge_attr):
        print("\n## Edge attr quick stats")
        names: List[str]
        if isinstance(edge_feature_names, (list, tuple)) and len(edge_feature_names) == edge_attr.size(1):
            names = [str(x) for x in edge_feature_names]
        else:
            names = [f"edge_attr[{i}]" for i in range(edge_attr.size(1))]
        rows = []
        ea = edge_attr.float()
        for i, name in enumerate(names):
            col = ea[:, i]
            rows.append([
                name,
                f"{nan_min(col):.4g}",
                f"{nan_max(col):.4g}",
                f"{nan_mean(col):.4g}",
            ])
        print_table(rows, ["feature", "min", "max", "mean"])


def inspect_one(path: Path) -> None:
    print("=" * 100)
    print(f"Inspecting: {path}")
    obj = load_pt(path)
    data = get_data(obj)
    metadata = get_metadata(obj)
    label_names = infer_label_names(obj, data)

    x = get_attr(data, "x", None)
    y = get_attr(data, "y", None)
    edge_index = get_attr(data, "edge_index", None)
    edge_attr = get_attr(data, "edge_attr", None)

    print("\n## Basic")
    print(f"num_nodes: {safe_num_nodes(data):,}")
    print(f"num_edges: {safe_num_edges(data):,}")
    print(f"x: {tensor_shape(x)}")
    print(f"y: {tensor_shape(y)}")
    print(f"edge_index: {tensor_shape(edge_index)}")
    print(f"edge_attr: {tensor_shape(edge_attr)}")
    if metadata:
        split_meta = metadata.get("split", {})
        protocol_meta = metadata.get("protocol", {})
        if isinstance(protocol_meta, dict) and protocol_meta.get("protocol"):
            print(f"protocol: {protocol_meta.get('protocol')}")
        if isinstance(split_meta, dict) and split_meta.get("type"):
            print(f"split_type: {split_meta.get('type')}")

    if torch.is_tensor(y):
        labeled = supervised_mask(y)
        print(f"labeled(supervised): {int(labeled.sum().item()):,}")
        print(f"supervised label classes: {int(torch.unique(y[labeled]).numel()) if labeled.any() else 0}")

        print("\n## Overall class distribution")
        print_table(class_counts(y, None, label_names), ["id", "label", "count"])

    feature_names = get_attr(data, "feature_names", None) or metadata.get("node_feature_columns")
    if isinstance(feature_names, (list, tuple)):
        print("\n## Node feature names")
        for i, name in enumerate(feature_names):
            print(f"{i:02d}: {name}")

    mask_summary(data, y if torch.is_tensor(y) else None, label_names)
    temporal_summary(data, metadata, y if torch.is_tensor(y) else None, label_names)

    print("\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=str, default=None, help="Path to one .pt file.")
    parser.add_argument("--data-dir", type=str, default=None, help="Directory containing protocol .pt files.")
    parser.add_argument("--out-root", type=str, default="experiments/runs", help="Timestamped archive root.")
    parser.add_argument("--no-save", action="store_true", help="Only print; do not save an archived report.")
    args = parser.parse_args()

    paths: List[Path] = []
    if args.path:
        paths.append(Path(args.path))
    if args.data_dir:
        paths.extend(sorted(Path(args.data_dir).glob("*.pt")))

    if not paths:
        raise SystemExit("Please provide --path FILE.pt or --data-dir DIR.")

    run = None if args.no_save else RunArtifacts.create("inspect_protocols", root=args.out_root)
    combined: List[str] = []
    for path in paths:
        if not path.exists():
            msg = f"[WARN] not found: {path}"
            print(msg)
            combined.append(msg)
            continue
        buf = StringIO()
        with redirect_stdout(buf):
            inspect_one(path)
        text = buf.getvalue()
        print(text, end="")
        combined.append(text)
        if run is not None:
            run.write_text(f"{path.stem}.md", text)
    if run is not None:
        run.write_text("inspect_protocols.md", "\n".join(combined))
        print(f"saved_log: {run.run_dir}")


if __name__ == "__main__":
    main()
