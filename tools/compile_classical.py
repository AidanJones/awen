"""Embed the small classical design library; no runtime fetch or build is required."""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def compile_library(check=False):
    data = json.loads((ROOT / 'research/classical-knowledge.json').read_text(encoding='utf-8'))
    assert data['version'] == '1.0.0' and len(data['presets']) == 9
    sources = {s['id'] for s in data['sources']}
    presets = {p['id'] for p in data['presets']}
    assert len(presets) == 9
    for preset in data['presets']:
        assert preset['evidenceStatus'] == 'awen-proposal'
        assert preset['sourceIds'] and set(preset['sourceIds']) <= sources
    for cue in data['cues']:
        assert cue['preset'] in presets and 0.5 <= cue['gate'] <= 1.15 and 0.3 <= cue['density'] <= 1
    block = '// CLASSICAL_LIBRARY_BEGIN\nconst CLASSICAL_LIBRARY=' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';\n// CLASSICAL_LIBRARY_END'
    path = ROOT / 'index.html'
    old = path.read_text(encoding='utf-8')
    new, count = re.subn(r'// CLASSICAL_LIBRARY_BEGIN[\s\S]*?// CLASSICAL_LIBRARY_END', lambda _: block, old)
    assert count == 1
    if check:
        assert new == old, 'Embedded classical library is stale'
    else:
        path.write_text(new, encoding='utf-8')
    return data


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    compile_library(parser.parse_args().check)
    print('Classical library matches the standalone reader.')
