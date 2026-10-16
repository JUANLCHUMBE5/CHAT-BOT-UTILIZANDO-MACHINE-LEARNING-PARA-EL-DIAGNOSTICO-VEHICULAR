"""Freeze the working backend/UI without modifying or committing concurrent work."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[2]
out = Path(sys.argv[1]).resolve()
out.mkdir(parents=True, exist_ok=False)
paths = subprocess.check_output(['git', '-C', str(root), 'ls-files', '-z', '--cached',
                                 '--others', '--exclude-standard', '--', 'backend', 'frontend'], text=True).split('\0')
manifest = {}
for name in paths:
    if not name:
        continue
    relative = Path(name)
    if any(part in {'__pycache__', 'node_modules', '.pytest_cache', '.ruff_cache', 'dist'}
           for part in relative.parts):
        continue
    if relative.parts[:2] in {('backend', 'data'), ('backend', 'logs'), ('backend', 'artifacts')}:
        continue
    if relative.name.startswith('.env') and relative.name != '.env.example':
        continue
    source = root / relative
    if not source.is_file() or source.suffix in {'.pyc', '.dump', '.gpg', '.pem', '.pkl'}:
        continue
    data = source.read_bytes()
    target = out / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    manifest[name] = hashlib.sha256(data).hexdigest()
for name, expected in manifest.items():
    if hashlib.sha256((root / name).read_bytes()).hexdigest() != expected:
        raise RuntimeError('Concurrent edit while creating snapshot: ' + name)
(out / 'source-manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
# Empty Git boundary prevents parent outputs/ ignores from disabling frontend lint.
# No commits, remotes or original Git metadata are copied.
subprocess.run(['git', '-C', str(out), '-c', 'init.defaultBranch=harness-snapshot',
                'init', '--quiet', '--template='], check=True)
print(out)



