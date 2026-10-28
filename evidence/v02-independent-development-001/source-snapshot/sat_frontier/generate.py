"""Deterministic generators; planted and random formulas stay distinct."""
import random
from .core import Formula

FAMILIES = ("random", "planted", "disconnected", "contradictory")


def generate(family, n, ratio, seed):
    if family not in FAMILIES or n < 3 or n > 256 or not 0 < ratio <= 20:
        raise ValueError("invalid generator parameters")
    rng = random.Random(seed)
    clauses = []
    plant = [rng.choice((False, True)) for _ in range(n)]
    for i in range(round(n*ratio)):
        pool = list(range(1, n+1))
        if family == "disconnected" and n >= 6:
            mid = n//2
            pool = list(range(1, mid+1)) if i % 2 else list(range(mid+1, n+1))
        vs = rng.sample(pool, 3)
        c = [v if rng.choice((False, True)) else -v for v in vs]
        if family == "planted" and not any(plant[abs(x)-1] == (x > 0) for x in c):
            c[0] *= -1
        clauses.append(tuple(c))
    if family == "contradictory":
        clauses.extend([(1,), (-1,)])
    return Formula(n, tuple(clauses))
