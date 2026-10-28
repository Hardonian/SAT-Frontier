"""Exact model counting. No pure-literal elimination: it loses models."""
from dataclasses import dataclass, asdict
from itertools import product
from time import perf_counter
import math


@dataclass(frozen=True)
class Formula:
    n: int
    clauses: tuple[tuple[int, ...], ...]

    def __post_init__(self):
        if type(self.n) is not int or self.n < 0:
            raise ValueError("n must be a nonnegative integer")
        for c in self.clauses:
            if any(type(x) is not int or x == 0 or abs(x) > self.n for x in c):
                raise ValueError("literal outside declared variable range")

    def dimacs(self):
        return f"p cnf {self.n} {len(self.clauses)}\n" + "".join(
            " ".join(map(str, c)) + (" " if c else "") + "0\n" for c in self.clauses)


def parse_dimacs(text):
    header = None
    tokens = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("c"):
            continue
        if line.startswith("p"):
            if header is not None or tokens:
                raise ValueError("duplicate or late header")
            parts = line.split()
            if len(parts) != 4 or parts[:2] != ["p", "cnf"]:
                raise ValueError("expected p cnf n m")
            header = tuple(map(int, parts[2:]))
            if min(header) < 0:
                raise ValueError("negative header")
        else:
            if header is None:
                raise ValueError("missing header")
            tokens.extend(map(int, line.split()))
    if header is None:
        raise ValueError("missing header")
    clauses, current = [], []
    for x in tokens:
        if x == 0:
            clauses.append(tuple(current))
            current = []
        else:
            current.append(x)
    if current or len(clauses) != header[1]:
        raise ValueError("unterminated clause or clause count mismatch")
    return Formula(header[0], tuple(clauses))


def canonical(clauses):
    out = set()
    for clause in clauses:
        c = frozenset(clause)
        if any(-x in c for x in c):
            continue
        out.add(tuple(sorted(c)))
    return tuple(sorted(out))


def oracle(f):
    """Independent exhaustive truth table; deliberately does not simplify CNF."""
    if f.n > 20:
        raise ValueError("oracle limited to 20 variables")
    return sum(all(any(bits[abs(x)-1] == (x > 0) for x in c)
                   for c in f.clauses) for bits in product((False, True), repeat=f.n))


class BudgetExceeded(Exception):
    pass


@dataclass
class Stats:
    nodes: int = 0
    unit_assignments: int = 0
    cache_hits: int = 0
    component_splits: int = 0
    cache_entries: int = 0


ALGORITHMS = {
    "baseline": (False, False, "occurrence"),
    "memo": (True, False, "occurrence"),
    "components": (False, True, "occurrence"),
    "combined": (True, True, "occurrence"),
    "balanced": (True, True, "balanced"),
}


POLICY_FEATURES = ("occurrence", "polarity", "short_clause", "component_size")


def validate_policy(policy):
    """Validate a closed, integer-only linear scoring schema (never code)."""
    if type(policy) is not dict or set(policy) != set(POLICY_FEATURES):
        raise ValueError("policy must contain exactly the four feature weights")
    if any(type(policy[k]) is not int or not -10 <= policy[k] <= 10
           for k in POLICY_FEATURES) or not any(policy.values()):
        raise ValueError("policy weights must be integers in [-10,10], not all zero")
    return dict(policy)


def policy_scores(cnf, policy, groups=None):
    """Return integer scores over active variables in a canonical residual CNF.

    Polarity is min(positive, negative), short incidence counts clauses of
    width at most two, component size is the incidence component's variables.
    """
    weights = validate_policy(policy)
    counts = {}
    for clause in cnf:
        for lit in clause:
            entry = counts.setdefault(abs(lit), [0, 0, 0])
            entry[lit > 0] += 1
            entry[2] += len(clause) <= 2
    sizes = {v: len(vs) for _, vs in (components(cnf) if groups is None else groups)
             for v in vs}
    return {v: (weights["occurrence"] * (negative + positive)
                + weights["polarity"] * min(negative, positive)
                + weights["short_clause"] * short
                + weights["component_size"] * sizes[v])
            for v, (negative, positive, short) in counts.items()}


def components(cnf):
    """Connected components of the variable-clause incidence graph."""
    owner = {}
    for i, c in enumerate(cnf):
        for x in c:
            owner.setdefault(abs(x), []).append(i)
    unseen = set(range(len(cnf)))
    groups = []
    while unseen:
        todo = [min(unseen)]
        unseen.remove(todo[0])
        indices, variables = [], set()
        while todo:
            i = todo.pop()
            indices.append(i)
            for x in cnf[i]:
                v = abs(x)
                if v in variables:
                    continue
                variables.add(v)
                for j in owner[v]:
                    if j in unseen:
                        unseen.remove(j)
                        todo.append(j)
        groups.append((tuple(cnf[i] for i in sorted(indices)), frozenset(variables)))
    return groups


def solve(f, algorithm="combined", seconds=5.0, max_nodes=1_000_000, cache_limit=100_000, *, branch_policy=None):
    if algorithm not in ALGORITHMS:
        raise ValueError("unknown algorithm")
    if not math.isfinite(seconds) or seconds <= 0 or max_nodes <= 0 or cache_limit < 0:
        raise ValueError("invalid budget")
    if branch_policy is not None:
        branch_policy = validate_policy(branch_policy)
        if algorithm != "combined":
            raise ValueError("custom policy requires combined algorithm")
    start = perf_counter()
    stats, cache = Stats(), {}
    memo, decompose, policy = ALGORITHMS[algorithm]

    def check():
        if perf_counter()-start >= seconds:
            raise BudgetExceeded("wall_limit")
        if stats.nodes >= max_nodes:
            raise BudgetExceeded("node_limit")

    def restrict(cnf, literal):
        out = []
        for c in cnf:
            check()
            if literal not in c:
                out.append(tuple(x for x in c if x != -literal))
        return canonical(out)

    def visit(cnf, remaining, depth=0):
        check()
        if depth >= 400:
            raise BudgetExceeded("depth_limit")
        stats.nodes += 1
        while True:
            if () in cnf:
                return 0
            if not cnf:
                return 1 << len(remaining)
            unit = next((c[0] for c in cnf if len(c) == 1), None)
            if unit is None:
                break
            remaining = remaining - {abs(unit)}
            stats.unit_assignments += 1
            cnf = restrict(cnf, unit)
        active = frozenset(abs(x) for c in cnf for x in c)
        free_factor = 1 << len(remaining-active)
        key = cnf
        if memo and key in cache:
            stats.cache_hits += 1
            return free_factor * cache[key]
        groups = components(cnf) if decompose else []
        if len(groups) > 1:
            stats.component_splits += 1
            result = 1
            for sub, variables in groups:
                result *= visit(sub, variables, depth+1)
                if result == 0:
                    break
        else:
            if branch_policy is not None:
                scores = policy_scores(cnf, branch_policy, groups)
                v = max(active, key=lambda x: (scores[x], -x))
            else:
                counts = {v: [0, 0] for v in active}
                for c in cnf:
                    for x in c:
                        counts[abs(x)][x > 0] += 1
                def score(v):
                    p, q = counts[v]
                    return ((p*q, p+q, -v) if policy == "balanced" else (p+q, -v))
                v = max(active, key=score)
            result = (visit(restrict(cnf, v), active-{v}, depth+1)
                      + visit(restrict(cnf, -v), active-{v}, depth+1))
        if memo and len(cache) < cache_limit:
            cache[key] = result
        return free_factor * result

    try:
        count = visit(canonical(f.clauses), frozenset(range(1, f.n+1)))
        status, reason = "exact", None
    except BudgetExceeded as exc:
        count, status, reason = None, "unknown", str(exc)
    except RecursionError:
        count, status = None, "unknown"
        reason = "recursion_limit"
    stats.cache_entries = len(cache)
    return dict(status=status, count=count, algorithm=algorithm, reason=reason,
                elapsed_seconds=perf_counter()-start, **asdict(stats))
