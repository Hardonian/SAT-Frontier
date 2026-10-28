#!/usr/bin/env python3
"""Static import/token inventory only; not a Lean dependency or axiom proof."""
from pathlib import Path
import hashlib, re, sys
root = Path(sys.argv[1]).resolve()
lean = root / 'lean'
start = 'OAI.Algorithms.SubexponentialSAT.Main'
todo = [start]
seen, missing, imports_external = set(), set(), set()
hits = []
while todo:
    mod = todo.pop()
    if mod in seen:
        continue
    seen.add(mod)
    path = lean / (mod.replace('.', '/') + '.lean')
    if not path.exists():
        missing.add(mod)
        continue
    text = path.read_text()
    for line in text.splitlines():
        match = re.match(r'^\s*import\s+([^\s]+)', line)
        if match:
            dep = match.group(1)
            if dep.startswith('OAI.'):
                todo.append(dep)
            else:
                imports_external.add(dep)
    for num, line in enumerate(text.splitlines(), 1):
        if re.search(r'\b(sorry|admit|axiom|unsafe|native_decide)\b', line):
            hits.append((mod, num, line.strip()))
print('root module:', start)
print('OAI import traversal modules:', len(seen), 'missing source:', len(missing))
print('missing:', *sorted(missing), sep='\n  ')
print('external import roots:', *sorted(imports_external), sep='\n  ')
print('lexical hits (may include comments; transitive external imports not scanned):', len(hits))
for mod, num, line in hits:
    print(f'{mod}:{num}: {line}')
print('\nSHA-256 of inspected key files:')
files = ['LICENSE','lean/LICENSE','lean/README.md','lean/ComparatorChallenges/README.md','lean/lean-toolchain','lean/lakefile.lean','lean/lake-manifest.json','lean/docs/378.md','lean/ComparatorChallenges/SubexponentialSAT.lean','lean/ComparatorChallenges/SubexponentialSAT.json','lean/OAI/Algorithms/SubexponentialSAT/Main.lean','lean/OAI/Algorithms/SubexponentialSAT/Encoding.lean','lean/OAI/Algorithms/SubexponentialSAT/Computation.lean','lean/OAI/Algorithms/SubexponentialSAT/Algorithm.lean','lean/OAI/Algorithms/SubexponentialSAT/SqrtLogSpace/Final.lean','lean/OAI/Algorithms/SubexponentialSAT/SqrtLog/ExecutionNativeFinal.lean','lean/OAI/Algorithms/SubexponentialSAT/SubexpOrderedRawMainTheorem.lean','preprints/The-Exponential-Time-Hypothesis-is-False-October-25-2026/paper.pdf']
for name in files:
    print(hashlib.sha256((root/name).read_bytes()).hexdigest(), name)
