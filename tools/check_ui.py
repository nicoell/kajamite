"""Verify shipped UI provenance without Node or frontend dependency installation."""
import hashlib
import json
from pathlib import Path


def check(root: Path) -> None:
    manifest = json.loads((root / 'src/kajamite/ui-build.json').read_text(encoding='utf-8'))
    if manifest.get('schema_version') != 1:
        raise ValueError('Unsupported UI build manifest')
    expected = {p.relative_to(root).as_posix() for p in (root / 'web').rglob('*')
                if p.is_file() and 'node_modules' not in p.parts}
    if expected != set(manifest['inputs']):
        raise ValueError('UI source list changed; run npm ci and npm run build in web/')
    outputs = {'src/kajamite/knowledge-change.html', 'src/kajamite/UI-NOTICES.txt'}
    if set(manifest['outputs']) != outputs:
        raise ValueError('Incomplete UI artifact manifest')
    for relative, digest in (manifest['inputs'] | manifest['outputs']).items():
        target = (root / relative).resolve()
        if not target.is_relative_to(root.resolve()):
            raise ValueError('UI manifest path escapes source root')
        data = target.read_text(encoding='utf-8').encode()
        if hashlib.sha256(data).hexdigest() != digest:
            raise ValueError(f'Stale UI artifact or source: {relative}; run npm ci and npm run build in web/')


if __name__ == '__main__':
    check(Path(__file__).resolve().parents[1])
    print('Packaged UI and source manifest match')
