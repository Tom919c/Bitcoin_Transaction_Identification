from __future__ import annotations

"""Aggregate campaign results and apply pre-registered sprint-1 verdicts.

Reads experiments/campaign/runs/*/metrics.csv (and metrics.json for GBDT),
builds the val comparison table and applies the frozen decision rules from
experiments/campaign/sprint1_prereg.yaml. Read-only; safe to run while the
queue trains.
"""

import csv
import json
from pathlib import Path

RUNS = Path('experiments/campaign/runs')
WATCH = ['GAMBLING_f1', 'EXCHANGE_f1', 'MARKETPLACE_f1', 'BRIDGE_f1']
PREREG = {
    'screen_no_go': -0.01,
    'dg_go_val': 0.020,
    'watch_drop_guard': 0.05,
    'dir_sage_beats_sage': 0.03,
    'dir_sage_within_egs': 0.02,
    'gbdt_band': 0.03,
}


def load_val_metrics(run_name: str) -> dict | None:
    path = RUNS / run_name / 'metrics.csv'
    if not path.exists():
        return None
    with open(path, encoding='utf-8') as f:
        rows = [r for r in csv.DictReader(f) if r['split'] == 'val']
    if not rows:
        return None
    return rows[-1]


def load_gbdt_val() -> list[dict]:
    path = RUNS / 'e2_gbdt_3seeds' / 'metrics.json'
    if not path.exists():
        return []
    with open(path, encoding='utf-8') as f:
        return [r for r in json.load(f) if r.get('split') == 'val']


def main() -> None:
    screen_names = {
        'A0_egs': 'screen_a0_egs_s42',
        'A1_resegs': 'screen_a1_s42',
        'A2_resegs': 'screen_a2_s42',
        'A3_lam0.1': 'screen_a3_lam0.1_s42',
        'A3_lam0.3': 'screen_a3_lam0.3_s42',
        'A3_lam1.0': 'screen_a3_lam1.0_s42',
    }
    vals: dict[str, dict] = {}
    for label, run in screen_names.items():
        row = load_val_metrics(run)
        if row is not None:
            vals[label] = row

    print('=== Sprint-1 screen (seed42, 80ep, val, temporal_balanced_no_temporal) ===')
    header = ['variant', 'macro_f1', 'd_vs_A0'] + WATCH + ['MIXER_f1']
    print(' | '.join(header))
    a0 = float(vals['A0_egs']['macro_f1']) if 'A0_egs' in vals else None
    for label in screen_names:
        if label not in vals:
            print(f'{label} | (pending)')
            continue
        row = vals[label]
        m = float(row['macro_f1'])
        d = m - a0 if a0 is not None else float('nan')
        cells = [f'{float(row[w]):.4f}' for w in WATCH]
        print(f"{label} | {m:.4f} | {d:+.4f} | " + ' | '.join(cells) + f" | {float(row['MIXER_f1']):.4f}")

    # Pre-registered screen verdicts.
    if a0 is not None:
        print('\n=== Verdicts (prereg:淘汰<-0.01; 晋级参考线>=+0.020) ===')
        for label in screen_names:
            if label == 'A0_egs' or label not in vals:
                continue
            d = float(vals[label]['macro_f1']) - a0
            if d < PREREG['screen_no_go']:
                verdict = 'NO-GO (eliminated)'
            elif d >= PREREG['dg_go_val']:
                verdict = 'PASS screen reference line'
            else:
                verdict = 'weak-positive (below promotion line)'
            drops = [w for w in WATCH if a0 and (float(vals['A0_egs'][w]) - float(vals[label][w])) > PREREG['watch_drop_guard']]
            if drops:
                verdict += f'; watch-class drop >0.05 in {drops}'
            print(f'{label}: d={d:+.4f} -> {verdict}')

    gbdt = load_gbdt_val()
    if gbdt and a0 is not None:
        import statistics
        gm = statistics.mean(float(r['macro_f1']) for r in gbdt)
        d = gm - a0
        if d >= PREREG['gbdt_band']:
            verdict = 'GBDT >= EGS+0.03: pause DG expansion, inspect feature drift'
        elif d <= -PREREG['gbdt_band']:
            verdict = 'graph still effective; continue DG-ResEGS'
        else:
            verdict = 'within band: both signals matter; no pure-topology attribution'
        print(f'\nGBDT val mean={gm:.4f} (n={len(gbdt)}) d_vs_A0={d:+.4f} -> {verdict}')

    # Formal (200ep) E0 anchors and Dir-SAGE, multi-seed.
    print('\n=== Formal val anchors (200ep, seeds 42/3407/1234) ===')
    for family, runs in {
        'E0_egs': ['e0_egs_s42', 'e0_egs_s3407', 'e0_egs_s1234'],
        'E1_dir_sage': ['e1_dir_sage_s42', 'e1_dir_sage_s3407', 'e1_dir_sage_s1234'],
    }.items():
        ms = []
        for run in runs:
            row = load_val_metrics(run)
            if row is not None:
                ms.append(float(row['macro_f1']))
                print(f'{run}: val macro_f1={ms[-1]:.4f}')
            else:
                print(f'{run}: (pending)')
        if len(ms) == len(runs):
            import statistics
            mean = statistics.mean(ms)
            sd = statistics.pstdev(ms)
            print(f'{family}: mean={mean:.4f} sd={sd:.4f}')
            if sd > 0.03:
                print(f'{family}: STABILITY WARNING sd>0.03; deltas <0.03 not interpretable as structural gains')


if __name__ == '__main__':
    main()
