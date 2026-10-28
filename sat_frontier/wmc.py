"""Weighted Model Counting (WMC) engine supporting exact rational arithmetic."""
from collections import defaultdict
from fractions import Fraction
from time import perf_counter


class WeightedFormula:
    """CNF formula with literal weights for exact probability computation."""

    def __init__(self, clauses, n_vars=None, weights=None):
        self.clauses = [sorted(set(c)) for c in clauses]
        used_vars = set(abs(lit) for c in self.clauses for lit in c)
        self.n_vars = max(used_vars) if used_vars else 0
        if n_vars is not None and n_vars > self.n_vars:
            self.n_vars = n_vars

        # Default literal weights: 1.0 (unweighted exact model counting)
        self.weights = {}
        if weights is not None:
            for lit, w in weights.items():
                self.weights[int(lit)] = Fraction(w) if not isinstance(w, Fraction) else w
        for v in range(1, self.n_vars + 1):
            if v not in self.weights:
                self.weights[v] = Fraction(1)
            if -v not in self.weights:
                self.weights[-v] = Fraction(1)

    def literal_weight(self, lit):
        return self.weights.get(lit, Fraction(1))

    def variable_sum(self, v):
        """Sum of positive and negative literal weights for a free variable."""
        return self.weights.get(v, Fraction(1)) + self.weights.get(-v, Fraction(1))

    def dimacs(self):
        """Standard DIMACS format with literal weights."""
        lines = [f"p cnf {self.n_vars} {len(self.clauses)}"]
        for v in range(1, self.n_vars + 1):
            lines.append(f"c p weight {v} {self.literal_weight(v)}")
            lines.append(f"c p weight {-v} {self.literal_weight(-v)}")
        for c in self.clauses:
            lines.append(" ".join(str(lit) for lit in c) + " 0")
        return "\n".join(lines) + "\n"


def wmc_oracle(wf, limit=16):
    """Exhaustive truth-table oracle for weighted model counting."""
    n = wf.n_vars
    if n > limit:
        raise ValueError(f"Oracle limit exceeded: {n} > {limit}")

    total_weight = Fraction(0)
    clauses = wf.clauses

    for mask in range(1 << n):
        # Assignment: True if bit is 1, False if 0
        sat = True
        for clause in clauses:
            if not any((lit > 0 and ((mask >> (lit - 1)) & 1)) or
                       (lit < 0 and not ((mask >> (abs(lit) - 1)) & 1))
                       for lit in clause):
                sat = False
                break
        if sat:
            # Multiply literal weights
            term = Fraction(1)
            for v in range(1, n + 1):
                if (mask >> (v - 1)) & 1:
                    term *= wf.literal_weight(v)
                else:
                    term *= wf.literal_weight(-v)
            total_weight += term

    return total_weight


def propagate_units(clauses, assigned_weight=None):
    """Iterative unit propagation tracking product of assigned literal weights."""
    cur_clauses = [list(c) for c in clauses]
    weight_mult = Fraction(1) if assigned_weight is None else assigned_weight
    units_applied = 0

    while True:
        unit = None
        for c in cur_clauses:
            if len(c) == 1:
                unit = c[0]
                break
        if unit is None:
            break

        units_applied += 1
        new_clauses = []
        contradiction = False
        for c in cur_clauses:
            if unit in c:
                continue  # Clause satisfied
            if -unit in c:
                reduced = [x for x in c if x != -unit]
                if not reduced:
                    contradiction = True
                    break
                new_clauses.append(reduced)
            else:
                new_clauses.append(c)

        if contradiction:
            return None, Fraction(0), units_applied
        cur_clauses = new_clauses

    return cur_clauses, weight_mult, units_applied


def find_components(clauses, active_vars):
    """Partition active variables and clauses into disconnected components."""
    if not clauses or not active_vars:
        return []

    var_to_clauses = defaultdict(list)
    for c_idx, c in enumerate(clauses):
        for lit in c:
            var_to_clauses[abs(lit)].append(c_idx)

    visited_vars = set()
    components = []

    for v in active_vars:
        if v in visited_vars:
            continue
        c_vars = set()
        c_clauses_idx = set()
        queue = [v]
        c_vars.add(v)
        visited_vars.add(v)

        while queue:
            curr = queue.pop()
            for c_idx in var_to_clauses[curr]:
                if c_idx not in c_clauses_idx:
                    c_clauses_idx.add(c_idx)
                    for lit in clauses[c_idx]:
                        nxt = abs(lit)
                        if nxt not in visited_vars:
                            visited_vars.add(nxt)
                            c_vars.add(nxt)
                            queue.append(nxt)

        comp_clauses = [clauses[idx] for idx in sorted(c_clauses_idx)]
        components.append((c_vars, comp_clauses))

    return components


def canonical_key(clauses):
    """Order-invariant tuple for component memoization."""
    return tuple(sorted(tuple(sorted(c)) for c in clauses))


def wmc_solve(wf, algorithm='combined_wmc', seconds=10.0, max_nodes=50000):
    """Solve Weighted Model Count with exact rational arithmetic and performance tracking."""
    start_time = perf_counter()
    nodes = 0
    cache_hits = 0
    splits = 0
    unit_assignments = 0
    cache = {}

    use_memo = algorithm in ('memo_wmc', 'combined_wmc')
    use_components = algorithm in ('components_wmc', 'combined_wmc', 'separator_wmc')
    use_separator = algorithm == 'separator_wmc'

    def count_component(clauses, active_vars):
        nonlocal nodes, cache_hits, splits, unit_assignments
        nodes += 1

        if nodes > max_nodes:
            raise RuntimeError("max_nodes_exceeded")
        if perf_counter() - start_time > seconds:
            raise TimeoutError("timeout_exceeded")

        # 1. Base cases
        if any(len(c) == 0 for c in clauses):
            return Fraction(0)
        if not clauses:
            # All remaining active variables are free
            res = Fraction(1)
            for v in active_vars:
                res *= wf.variable_sum(v)
            return res

        # 2. Free variables present in active_vars but absent from any clause
        present_vars = set(abs(lit) for c in clauses for lit in c)
        free_factor = Fraction(1)
        for v in (active_vars - present_vars):
            free_factor *= wf.variable_sum(v)
        active_vars = present_vars

        # 3. Unit propagation
        unit_literal = None
        for c in clauses:
            if len(c) == 1:
                unit_literal = c[0]
                break

        if unit_literal is not None:
            unit_assignments += 1
            var = abs(unit_literal)
            new_clauses = []
            for c in clauses:
                if unit_literal in c:
                    continue
                if -unit_literal in c:
                    red = [x for x in c if x != -unit_literal]
                    if not red:
                        return Fraction(0)
                    new_clauses.append(red)
                else:
                    new_clauses.append(c)

            sub_weight = count_component(new_clauses, active_vars - {var})
            return free_factor * wf.literal_weight(unit_literal) * sub_weight

        # 4. Check cache if memoization enabled
        key = None
        if use_memo:
            key = canonical_key(clauses)
            if key in cache:
                cache_hits += 1
                return free_factor * cache[key]

        # 5. Connected component decomposition
        if use_components:
            comps = find_components(clauses, active_vars)
            if len(comps) > 1:
                splits += len(comps) - 1
                total = Fraction(1)
                for c_vars, c_clauses in comps:
                    total *= count_component(c_clauses, c_vars)
                ans = free_factor * total
                if use_memo and key is not None:
                    cache[key] = total
                return ans

        # 6. Branching selection
        branch_var = None
        if use_separator:
            # Check articulation points in the incidence/primal graph
            from .separator import find_separator_variable
            branch_var = find_separator_variable(clauses, active_vars)

        if branch_var is None:
            # DLCS heuristic: select variable with maximum appearances in shortest clauses
            min_len = min(len(c) for c in clauses)
            candidates = [c for c in clauses if len(c) == min_len]
            counts = defaultdict(int)
            for c in candidates:
                for lit in c:
                    counts[abs(lit)] += 1
            branch_var = max(active_vars, key=lambda v: (counts[v], v))

        # Branch positive: assign branch_var = True
        pos_clauses = []
        for c in clauses:
            if branch_var in c:
                continue
            if -branch_var in c:
                red = [x for x in c if x != -branch_var]
                pos_clauses.append(red)
            else:
                pos_clauses.append(c)
        pos_res = count_component(pos_clauses, active_vars - {branch_var})
        pos_weight = wf.literal_weight(branch_var) * pos_res

        # Branch negative: assign branch_var = False
        neg_clauses = []
        for c in clauses:
            if -branch_var in c:
                continue
            if branch_var in c:
                red = [x for x in c if x != branch_var]
                neg_clauses.append(red)
            else:
                neg_clauses.append(c)
        neg_res = count_component(neg_clauses, active_vars - {branch_var})
        neg_weight = wf.literal_weight(-branch_var) * neg_res

        ans = free_factor * (pos_weight + neg_weight)
        if use_memo and key is not None:
            cache[key] = pos_weight + neg_weight
        return ans

    try:
        all_vars = set(range(1, wf.n_vars + 1))
        exact_weight = count_component(wf.clauses, all_vars)
        elapsed = perf_counter() - start_time
        return {
            'status': 'exact',
            'weight_fraction': str(exact_weight),
            'weight_float': float(exact_weight),
            'nodes': nodes,
            'cache_hits': cache_hits,
            'component_splits': splits,
            'unit_assignments': unit_assignments,
            'elapsed_seconds': elapsed,
            'algorithm': algorithm,
            'cache_entries': len(cache),
        }
    except RuntimeError as exc:
        return {
            'status': 'unknown',
            'reason': 'max_nodes_exceeded',
            'weight_fraction': None,
            'weight_float': None,
            'nodes': nodes,
            'elapsed_seconds': perf_counter() - start_time,
            'algorithm': algorithm,
        }
    except TimeoutError as exc:
        return {
            'status': 'unknown',
            'reason': 'timeout_exceeded',
            'weight_fraction': None,
            'weight_float': None,
            'nodes': nodes,
            'elapsed_seconds': perf_counter() - start_time,
            'algorithm': algorithm,
        }
