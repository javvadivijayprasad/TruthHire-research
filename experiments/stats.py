"""Mean and 95% confidence interval across seeds (normal approximation)."""
from __future__ import annotations
import math
from typing import List, Tuple


def mean_ci(xs: List[float]) -> Tuple[float, float, float]:
    n = len(xs)
    if n == 0:
        return 0.0, 0.0, 0.0
    m = sum(xs) / n
    if n == 1:
        return m, m, m
    var = sum((x - m) ** 2 for x in xs) / (n - 1)
    half = 1.96 * math.sqrt(var / n)
    return m, m - half, m + half
