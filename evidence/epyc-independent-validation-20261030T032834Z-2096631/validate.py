"""Independent grid connectivity transfer DP and tiny brute-force checks."""
from collections import defaultdict
from fractions import Fraction
from itertools import product
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def edges(rows, cols):
    # Column order minimizes live frontier; independent of CNF variable order.
    out = []
    for c in range(cols):
        for r in range(rows - 1):
            out.append(((r,c),(r+1,c)))
        if c + 1 < cols:
            for r in range(rows):
                out.append(((r,c),(r,c+1)))
    return out

def canonical(groups):
    return tuple(sorted(tuple(sorted(g)) for g in groups))

def transfer(rows, cols):
    es = edges(rows, cols)
    s, t = (0,0), (rows-1,cols-1)
    last = {v:i for i,e in enumerate(es) for v in e}
    states = {canonical([{s}, {t}] if s != t else [{s}]): 1}
    for i, (u,v) in enumerate(es):
        nxt = defaultdict(int)
        for state, mass in states.items():
            groups = [set(g) for g in state]
            known = set().union(*groups)
            for x in (u,v):
                if x not in known:
                    groups.append({x}); known.add(x)
            for opened, multiplier in ((False,1),(True,9)):
                gs = [g.copy() for g in groups]
                if opened:
                    a = next(j for j,g in enumerate(gs) if u in g)
                    b = next(j for j,g in enumerate(gs) if v in g)
                    if a != b:
                        gs[a].update(gs[b]); gs.pop(b)
                for g in gs:
                    g.difference_update(x for x in list(g) if x not in (s,t) and last[x] == i)
                nxt[canonical(g for g in gs if g)] += mass * multiplier
        states = nxt
    total = sum(m for state,m in states.items() if any(s in g and t in g for g in state))
    return Fraction(total, 10**len(es))

def brute(rows, cols):
    es = edges(rows,cols); s=(0,0); t=(rows-1,cols-1); total=0
    for bits in product((0,1), repeat=len(es)):
        seen={s}; changed=True
        while changed:
            changed=False
            for (u,v),on in zip(es,bits):
                if on and ((u in seen) != (v in seen)):
                    seen.update((u,v)); changed=True
        if t in seen:
            total += 9**sum(bits)
    return Fraction(total,10**len(es))

for rows, cols in [(2,2),(2,3),(3,3)]:
    actual, oracle = transfer(rows,cols), brute(rows,cols)
    assert actual == oracle, (rows,cols,actual,oracle)
    print(f'brute-force {rows}x{cols}: MATCH {actual}')
value=transfer(3,10)
print('independent grid_3x10:', value)
for d in (6,8):
    p=ROOT / 'evidence/epyc-crossdepth-20261030T032834Z-2096631/results' / f'grid_3x10_d{d}_w4.json'
    data=json.loads(p.read_text()); assert data['status']=='exact'
    assert Fraction(data['weight_fraction']) == value
    print(f'CNF solver depth {d}: MATCH')
print('Scope: independent graph connectivity algorithm; comparison assumes the pinned CNF represents that same grid.')
