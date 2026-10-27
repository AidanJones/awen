"""Package a standalone, model-free nine-direction listening playground."""
import argparse
import hashlib
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build(output, paired_url=None, previous_url=None):
    html = (ROOT / 'index.html').read_text(encoding='utf-8')
    runtime = re.search(r'<script>\s*([\s\S]*?)</script>', html)[1].split('const $=id=>')[0]
    books = json.loads(re.search(r'<script id="books"[^>]*>([\s\S]*?)</script>', html)[1])
    library = json.loads((ROOT / 'research/scoring-knowledge.json').read_text(encoding='utf-8'))
    suite = json.loads((ROOT / 'research/calibration-scenes.json').read_text(encoding='utf-8'))
    scenes = []
    for entry in suite['scenes']:
        book = next(b for b in books if b['id'] == entry['book'])
        chapter = next(c for c in book['chapters'] if c['id'] == entry['chapter'])
        i = entry['paragraph'] - 1
        scenes.append(dict(id=entry['id'], book={k: book[k] for k in ('id', 'title', 'author', 'url', 'license')},
                           chapter=chapter['title'], text=chapter['paragraphs'][i],
                           context=chapter['paragraphs'][i-1] if entry.get('preceding') else ''))
    fingerprint = hashlib.sha256(runtime.encode()).hexdigest()
    data = dict(version=1, engineSha256=fingerprint, library=library, scenes=scenes, pairedUrl=paired_url, previousUrl=previous_url)
    template = (ROOT / 'tools/exploration-review.html').read_text(encoding='utf-8')
    page = template.replace('__EXPLORATION_DATA__', json.dumps(data, ensure_ascii=False).replace('<', '\\u003c'))
    page = page.replace('__PRODUCTION_RUNTIME__', runtime)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    (output / 'explore.html').write_text(page, encoding='utf-8')
    manifest = dict(version=1, engineSha256=fingerprint, pageSha256=hashlib.sha256(page.encode()).hexdigest(),
                    createdAt=datetime.now(timezone.utc).isoformat(), scenes=[s['id'] for s in scenes])
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    return output / 'explore.html'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, help='New output directory (never overwritten)')
    parser.add_argument('--paired-url', help='Optional link back to a separate paired review')
    parser.add_argument('--previous-url', help='Optional earlier explorer; keeps its sounds and backups available')
    args = parser.parse_args()
    output = args.output or ROOT / '.score-lab/exploration' / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex)
    print(build(output, args.paired_url, args.previous_url).resolve())
