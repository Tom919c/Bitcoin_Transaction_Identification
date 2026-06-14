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

LEGACY_LABELS_5 = ['INDIVIDUAL', 'BET', 'GAMBLING', 'EXCHANGE', 'BRIDGE']

LABEL_TO_ID_11 = {label: idx for idx, label in enumerate(RAW_LABELS_11)}
ID_TO_LABEL_11 = {idx: label for label, idx in LABEL_TO_ID_11.items()}
LABEL_TO_ID_5 = {label: idx for idx, label in enumerate(LEGACY_LABELS_5)}
ID_TO_LABEL_5 = {idx: label for label, idx in LABEL_TO_ID_5.items()}

# For old data.pt compatibility where NONE=0 and supervised labels are 1..5.
LEGACY_RAW_TO_NAME = {
    0: 'NONE',
    1: 'INDIVIDUAL',
    2: 'BET',
    3: 'GAMBLING',
    4: 'EXCHANGE',
    5: 'BRIDGE',
}

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
    if label_space == '11':
        return LABEL_TO_ID_11.get(label, UNKNOWN_LABEL)
    if label_space == '5':
        return LABEL_TO_ID_5.get(label, UNKNOWN_LABEL)
    raise ValueError(f'Unknown label_space: {label_space}')


def id_to_label(idx: int, label_space: str = '11') -> str:
    if idx == UNKNOWN_LABEL:
        return 'UNKNOWN'
    if label_space == '11':
        return ID_TO_LABEL_11[int(idx)]
    if label_space == '5':
        return ID_TO_LABEL_5[int(idx)]
    raise ValueError(f'Unknown label_space: {label_space}')


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
    if name == '11':
        return LabelSpace('11', RAW_LABELS_11)
    if name == '5':
        return LabelSpace('5', LEGACY_LABELS_5)
    raise ValueError(name)
