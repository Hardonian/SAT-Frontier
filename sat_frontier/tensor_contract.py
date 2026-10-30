"""Tensor Network Contraction for exact counting (#SAT) and Weighted Model Counting (#WMC).

Maps CNF formulas and variable weights to tensor networks, contracting them via
NumPy einsum, PyTorch einsum (CPU / GPU), or heuristic min-degree bucket elimination.
"""
from collections import defaultdict
from fractions import Fraction
import string
from time import perf_counter

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    np = None  # type: ignore[assignment]
    HAS_NUMPY = False

try:
    import torch
    HAS_TORCH = True
except ImportError:
    torch = None  # type: ignore[assignment]
    HAS_TORCH = False


def build_cnf_tensors(clauses, n_vars, weights=None, backend='numpy', device='cpu'):
    """Compile CNF clauses and weights into a list of (tensor, variable_indices) pairs.

    Each clause C becomes a rank-k boolean tensor where element is 0 at the single
    falsifying assignment and 1 everywhere else.
    Each variable v has a rank-1 prior/weight tensor [w(-v), w(+v)].
    """
    if backend == 'torch' and not HAS_TORCH:
        raise ImportError("PyTorch is required for backend='torch'.")
    if backend == 'numpy' and not HAS_NUMPY:
        raise ImportError("NumPy is required for backend='numpy'.")

    use_torch = (backend == 'torch')
    tensors = []

    # 1. Clause tensors
    for clause in clauses:
        vars_in_c = sorted(set(abs(lit) for lit in clause))
        k = len(vars_in_c)
        if k == 0:
            # Empty clause: always UNSAT
            shape = ()
            if use_torch:
                t = torch.tensor(0.0, dtype=torch.float64, device=device)
            else:
                t = np.array(0.0, dtype=np.float64)
            tensors.append((t, ()))
            continue

        lits = set(clause)
        # Check for tautology (both x and -x in clause) -> always satisfied (all 1s)
        if any(-lit in lits for lit in lits):
            continue

        var_to_pos = {v: i for i, v in enumerate(vars_in_c)}
        shape = (2,) * k
        if use_torch:
            t = torch.ones(shape, dtype=torch.float64, device=device)
        else:
            t = np.ones(shape, dtype=np.float64)

        falsifying = [0] * k
        for lit in clause:
            v = abs(lit)
            falsifying[var_to_pos[v]] = 0 if lit > 0 else 1
        t[tuple(falsifying)] = 0.0
        tensors.append((t, tuple(vars_in_c)))

    # 2. Variable weight/prior tensors
    for v in range(1, n_vars + 1):
        w_pos = float(weights[v]) if weights and v in weights else 1.0
        w_neg = float(weights[-v]) if weights and -v in weights else 1.0

        if use_torch:
            w = torch.tensor([w_neg, w_pos], dtype=torch.float64, device=device)
        else:
            w = np.array([w_neg, w_pos], dtype=np.float64)
        tensors.append((w, (v,)))

    return tensors


def contract_einsum(tensors, backend='numpy', device='cpu'):
    """Contract tensor network using a single global einsum expression (up to 52 variables)."""
    if not tensors:
        return 1.0

    all_vars = sorted(set(idx for _, idxs in tensors for idx in idxs))
    if len(all_vars) > 52:
        raise ValueError(f"einsum mode supports up to 52 variables; got {len(all_vars)}.")

    chars = string.ascii_letters  # 52 distinct letters
    var_map = {v: chars[i] for i, v in enumerate(all_vars)}

    subs_in = ','.join(''.join(var_map[idx] for idx in idxs) for _, idxs in tensors)
    subscripts = f"{subs_in}->"

    raw_tensors = [t for t, _ in tensors]

    if backend == 'torch' and HAS_TORCH:
        res = torch.einsum(subscripts, *raw_tensors)
        return float(res.item()) if hasattr(res, 'item') else float(res)
    elif backend == 'numpy' and HAS_NUMPY:
        res = np.einsum(subscripts, *raw_tensors, optimize='greedy')
        return float(res.item()) if hasattr(res, 'item') else float(res)
    else:
        raise RuntimeError("No tensor backend available.")


def contract_bucket_elimination(tensors, n_vars, backend='numpy', device='cpu'):
    """Contract tensor network via min-degree variable elimination."""
    use_torch = (backend == 'torch') and HAS_TORCH
    curr_tensors = list(tensors)

    # Compute initial variable degrees
    var_degrees = defaultdict(int)
    for _, idxs in curr_tensors:
        for v in idxs:
            var_degrees[v] += 1

    elim_order = sorted(range(1, n_vars + 1), key=lambda v: var_degrees[v])

    for v in elim_order:
        matching = []
        remaining = []
        for t, idxs in curr_tensors:
            if v in idxs:
                matching.append((t, idxs))
            else:
                remaining.append((t, idxs))

        if not matching:
            continue

        # Eliminate variable v from matching tensors
        all_local_vars = sorted(set(idx for _, idxs in matching for idx in idxs))
        out_vars = [idx for idx in all_local_vars if idx != v]

        chars = string.ascii_letters
        if len(all_local_vars) > len(chars):
            raise RuntimeError(f"Intermediate cluster exceeds {len(chars)} variables.")

        local_map = {var_id: chars[i] for i, var_id in enumerate(all_local_vars)}
        subs_in = ','.join(''.join(local_map[idx] for idx in idxs) for _, idxs in matching)
        sub_out = ''.join(local_map[idx] for idx in out_vars)
        subscripts = f"{subs_in}->{sub_out}"

        raw_matching = [t for t, _ in matching]
        if use_torch:
            contracted = torch.einsum(subscripts, *raw_matching)
        else:
            contracted = np.einsum(subscripts, *raw_matching, optimize='greedy')

        remaining.append((contracted, tuple(out_vars)))
        curr_tensors = remaining

    total = 1.0
    for t, idxs in curr_tensors:
        if use_torch:
            val = float(t.item()) if hasattr(t, 'item') else float(t)
        else:
            val = float(t.item()) if hasattr(t, 'item') else float(t)
        total *= val

    return total


def tensor_solve(f, weights=None, backend='numpy', device='cpu', mode='auto'):
    """Solve exact count or WMC using Tensor Network Contraction.

    Parameters
    ----------
    f : Formula or WeightedFormula
        The CNF formula to evaluate.
    weights : dict, optional
        Literal weights mapping int -> Fraction or float.
    backend : str
        'numpy' (default) or 'torch'.
    device : str
        'cpu' (default) or 'cuda' (for GPU acceleration when supported).
    mode : str
        'auto' (default), 'einsum', or 'bucket_elimination'.
    """
    start_time = perf_counter()
    n_vars = getattr(f, 'n_vars', getattr(f, 'n', 0))
    clauses = f.clauses

    # If backend is torch and device is cuda, verify device works before proceeding
    actual_device = device
    if backend == 'torch' and device == 'cuda':
        if not HAS_TORCH or not torch.cuda.is_available():
            raise RuntimeError("CUDA device requested but torch.cuda.is_available() is False.")
        try:
            _ = torch.zeros(1, device='cuda')
        except Exception as e:
            raise RuntimeError(f"GPU device test failed: {e}")

    tensors = build_cnf_tensors(
        clauses, n_vars, weights=weights, backend=backend, device=actual_device
    )

    if mode == 'auto':
        mode = 'einsum' if n_vars <= 20 else 'bucket_elimination'

    if mode == 'einsum':
        raw_val = contract_einsum(tensors, backend=backend, device=actual_device)
    elif mode == 'bucket_elimination':
        raw_val = contract_bucket_elimination(tensors, n_vars, backend=backend, device=actual_device)
    else:
        raise ValueError(f"Unknown contraction mode: {mode}")

    elapsed = perf_counter() - start_time

    if weights is None:
        int_count = int(round(raw_val))
        return {
            'status': 'exact',
            'count': int_count,
            'float_val': raw_val,
            'backend': backend,
            'device': actual_device,
            'mode': mode,
            'elapsed_seconds': elapsed,
        }
    else:
        return {
            'status': 'exact',
            'weight_float': raw_val,
            'backend': backend,
            'device': actual_device,
            'mode': mode,
            'elapsed_seconds': elapsed,
        }
