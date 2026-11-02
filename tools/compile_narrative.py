"""Authoring-only dictionary embed; the distributed HTML needs no build or fetch."""
import argparse
import json
import re

from narrative_dictionary import ROOT, LIBRARY, validate_library


def compile_library(check=False):
    data = validate_library(json.loads(LIBRARY.read_text(encoding='utf-8')))
    block = '// NARRATIVE_LIBRARY_BEGIN\nconst NARRATIVE_LIBRARY=' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';\n// NARRATIVE_LIBRARY_END'
    path = ROOT / 'index.html'
    old = path.read_text(encoding='utf-8')
    new, count = re.subn(r'// NARRATIVE_LIBRARY_BEGIN[\s\S]*?// NARRATIVE_LIBRARY_END', lambda _: block, old)
    if count != 1:
        raise ValueError('Expected one narrative embedding marker')
    if check:
        if new != old:
            raise ValueError('Reader dictionary is stale')
    else:
        path.write_text(new, encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    compile_library(parser.parse_args().check)
    print('Narrative dictionary matches standalone reader.')
