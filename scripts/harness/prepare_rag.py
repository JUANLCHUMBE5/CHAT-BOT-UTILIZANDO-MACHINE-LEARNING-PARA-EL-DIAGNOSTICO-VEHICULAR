"""Stage the committed RAG bytes; never normalize or rebuild frozen source artifacts."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[2]
out = Path(sys.argv[1]).resolve()
out.mkdir(parents=True, exist_ok=False)
source = 'machine_learning/manuals/candidates/v1'
paths = subprocess.check_output(['git', '-C', str(root), 'ls-tree', '-r', '--name-only',
                                 'HEAD', '--', source], text=True).splitlines()
for path in paths:
    target = out / Path(path).relative_to(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(subprocess.check_output(['git', '-C', str(root), 'show', 'HEAD:' + path]))
manifest = json.loads((out / 'manifests/verified_frozen_bundle.json').read_text(encoding='utf-8'))
checked = dict(manifest['files'])
checked['indexes/indice_faiss_v1.index'] = manifest['index_sha256']
differences = []
for name, expected in checked.items():
    if hashlib.sha256((out / name).read_bytes()).hexdigest() != expected:
        raise RuntimeError('Committed package mismatch: ' + name)
    if hashlib.sha256((root / source / name).read_bytes()).hexdigest() != expected:
        differences.append(name)
(out.parent / 'rag-staging.json').write_text(json.dumps({
    'source_commit': subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip(),
    'verified_files': len(checked), 'working_tree_byte_differences': differences,
    'index_rebuilt': False, 'original_files_modified': False,
}, indent=2), encoding='utf-8')
print(out)

