from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EarlyStopping:
    patience: int = 50
    mode: str = 'max'
    best: float | None = None
    bad_epochs: int = 0

    def step(self, value: float) -> bool:
        if self.best is None or (value > self.best if self.mode == 'max' else value < self.best):
            self.best = value
            self.bad_epochs = 0
            return False
        self.bad_epochs += 1
        return self.bad_epochs >= self.patience
