from __future__ import annotations

from dataclasses import dataclass

UNKNOWN_LABEL = -1

RAW_LABELS_11 = [
    'INDIVIDUAL',
    'BET',
    'GAMBLING',
    'EXCHANGE',
    'MINING',
    'PONZI',
    'RANSOMWARE',
    'FAUCET',
    'MARKETPLACE',
    'MIXER',
    'BRIDGE',
]

LABEL_TO_ID_11 = {label: idx for idx, label in enumerate(RAW_LABELS_11)}
ID_TO_LABEL_11 = {idx: label for label, idx in LABEL_TO_ID_11.items()}

RISK_GROUPS = {
    # Strict AML-sensitive group. Conservative and safest for papers.
    'conservative_sensitive': ['PONZI', 'RANSOMWARE', 'MIXER'],
    # Includes gambling/betting and bridge as sensitive but not legally "illegal".
    'extended_sensitive': ['PONZI', 'RANSOMWARE', 'MIXER', 'BET', 'GAMBLING', 'MARKETPLACE', 'BRIDGE'],
    # Service/neutral references. Do not call all of them legal or benign.
    'neutral_reference': ['INDIVIDUAL', 'EXCHANGE', 'MINING', 'FAUCET'],
}


def normalize_label(label: object) -> str:
    if label is None:
        return ''
    return str(label).strip().upper()


def map_label(label: object, label_space: str = '11') -> int:
    label = normalize_label(label)
    if label in {'', 'NONE', 'NULL', 'NAN'}:
        return UNKNOWN_LABEL
    if label_space != '11':
        raise ValueError(f'Only label_space=11 is supported in the current code path, got: {label_space}')
    return LABEL_TO_ID_11.get(label, UNKNOWN_LABEL)


def id_to_label(idx: int, label_space: str = '11') -> str:
    if idx == UNKNOWN_LABEL:
        return 'UNKNOWN'
    if label_space != '11':
        raise ValueError(f'Only label_space=11 is supported in the current code path, got: {label_space}')
    return ID_TO_LABEL_11[int(idx)]


def risk_binary_label(label_name: str, group: str = 'conservative_sensitive') -> int:
    label_name = normalize_label(label_name)
    return int(label_name in set(RISK_GROUPS[group]))


@dataclass(frozen=True)
class LabelSpace:
    name: str
    labels: list[str]

    @property
    def num_classes(self) -> int:
        return len(self.labels)


def get_label_space(name: str = '11') -> LabelSpace:
    if name != '11':
        raise ValueError(f'Only label_space=11 is supported in the current code path, got: {name}')
    return LabelSpace('11', RAW_LABELS_11)
