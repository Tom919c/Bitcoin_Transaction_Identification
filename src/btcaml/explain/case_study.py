from __future__ import annotations


def format_case_study(alias, pred_label, confidence, top_edges=None) -> str:
    lines = [f'# Case Study: {alias}', '', f'- Predicted label: {pred_label}', f'- Confidence: {confidence:.4f}']
    if top_edges is not None:
        lines.append('- Top explanatory edges are available in the attached table/object.')
    return '\n'.join(lines)
