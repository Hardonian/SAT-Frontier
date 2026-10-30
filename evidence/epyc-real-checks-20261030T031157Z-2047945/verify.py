import csv, hashlib, itertools, json, subprocess
from fractions import Fraction
from pathlib import Path

root = Path(__file__).resolve().parents[2]
checks = Path(__file__).resolve().parent
studies = ['epyc-real-pilot-20261030T031116Z-2045642', 'epyc-real-next-20261030T031157Z-2047945']
historical = root/'evidence/cut-cube-001/runs.csv'
old = list(csv.DictReader(historical.open()))
report = {'historical_csv_sha256': hashlib.sha256(historical.read_bytes()).hexdigest(), 'studies': {}, 'note': 'Historical weights are comparisons to prior runs, not independent solver checks. Barbell oracle uses independent exhaustive evaluation and signed input weights, not probabilities.'}
manifest = json.loads((root/'instances/epyc-cut-frontier/manifest.json').read_text())
for study in studies:
    directory = root/'evidence'/study
    cp = subprocess.run(['sha256sum','-c','SHA256SUMS'], cwd=directory, text=True, capture_output=True)
    if cp.returncode: raise RuntimeError(cp.stdout + cp.stderr)
    rows = list(csv.DictReader((directory/'runs.csv').open()))
    comparisons = []
    inputs = {}
    for row in rows:
        name = row['instance']
        if name != 'barbell_6_3_6':
            candidates = [r for r in old if r['instance_label'] == name and r['status'] == 'exact']
            if not candidates or any(Fraction(r['weight_fraction']) != Fraction(row['weight_fraction']) for r in candidates):
                raise AssertionError('historical mismatch ' + name)
            comparisons.append({'instance': name, 'depth': row['depth'], 'historical_exact_matches': len(candidates)})
        instance = root/'instances/epyc-cut-frontier'/f'{name}.cnf'
        h = hashlib.sha256(instance.read_bytes()).hexdigest()
        if h != manifest[name]['sha256'] or h != row['instance_sha256']: raise AssertionError('input mismatch '+name)
        inputs[name] = h
    report['studies'][study] = {'checksum_entries_verified': len(cp.stdout.splitlines()), 'input_sha256': inputs, 'historical_comparisons': comparisons, 'summary': json.loads((directory/'summary.json').read_text())}
source = root/'instances/epyc-cut-frontier/barbell_6_3_6.cnf'
clauses = [list(map(int, line.split()[:-1])) for line in source.read_text().splitlines() if line and line[0] not in 'cp']
groups = [[c for c in clauses if min(c) >= lo and max(c) <= lo+14] for lo in (1,16)]
assert len(groups[0]) == len(groups[1]) == 16 and [31] in clauses and len(clauses)==33
sums = []
for lo, group in zip((1,16), groups):
    total = 0
    for bits in itertools.product((0,1), repeat=15):
        if all(any(bits[v-lo] for v in clause) for clause in group):
            k = sum(bits)
            total += 3**k * (-2)**(15-k)
    sums.append(total)
value = Fraction(sums[0]*sums[1]*9,10)
pilot = list(csv.DictReader((root/'evidence'/studies[0]/'runs.csv').open()))
for row in pilot:
    if row['instance'] == 'barbell_6_3_6': assert Fraction(row['weight_fraction']) == value
report['barbell_exhaustive_oracle'] = {'factor_sums': sums, 'fraction': str(value), 'pilot_depths_matched': [r['depth'] for r in pilot if r['instance'] == 'barbell_6_3_6'], 'weights': 'variables 1..30: true=3 false=-2; variable 31: true=9/10 false=1/10', 'warning': 'Signed weights yield a weighted sum, not network reliability; historical barbell_k6 used different weights and cannot be compared.'}
out = checks/'verification.json'
if out.exists(): raise FileExistsError(out)
out.write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
