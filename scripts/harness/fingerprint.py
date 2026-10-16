"""Detect source changes while a harness is running, without altering the checkout."""
import hashlib
import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[2]
paths = ('backend/src', 'backend/tests', 'backend/scripts/lab', 'frontend/src',
         'frontend/tests/harness', 'frontend/lab', 'machine_learning/tests')
files = sorted({p for folder in paths for p in (root / folder).rglob('*')
                if p.is_file() and p.suffix in {'.py', '.ts', '.tsx', '.js', '.html'}
                and '__pycache__' not in p.parts} | {root / 'backend/main.py'})
current = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
target = Path(sys.argv[1])
if len(sys.argv) > 2 and sys.argv[2] == '--compare':
    before = json.loads(target.read_text(encoding='utf-8'))
    changed = [p for p in before.keys() | current.keys() if before.get(p) != current.get(p)]
    if changed:
        raise RuntimeError('Source changed during validation: ' + ', '.join(changed))
    print('Source fingerprint stable')
else:
    target.write_text(json.dumps(current, indent=2), encoding='utf-8')
