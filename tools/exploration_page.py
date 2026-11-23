"""Package a standalone, model-free nine-direction listening playground."""
import argparse
import hashlib
import json
import re
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]


def build(output, paired_url=None, previous_url=None, reader_url=None, include_reader=False, initial_set='broad', review_public=None, previous_page=None):
    if initial_set not in ['broad','bach','classical','adventure']: raise ValueError('Unknown initial set')
    if reader_url and (urlsplit(reader_url).scheme not in ('', 'http', 'https') or reader_url.startswith('//') or any(ord(c)<32 for c in reader_url)):
        raise ValueError('Reader link must be relative or HTTP(S)')
    html = (ROOT / 'index.html').read_text(encoding='utf-8')
    if include_reader and reader_url is None:
        reader_url = 'index.html?explorer=explore.html'
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
    adventure = json.loads((ROOT/'research/adventure-starting-score.json').read_text(encoding='utf8'))
    if review_public:
        review_public=Path(review_public).resolve()
        if not (review_public/'review.html').is_file() or (review_public/'private-key.json').exists(): raise ValueError('Use the original review public folder')
        packet=json.loads(re.search(r'id="calibration-data"[^>]*>(.*?)</script>',(review_public/'review.html').read_text(encoding='utf8'),re.S)[1])
        if packet['packetSha256']!=adventure['reviewPacketSha256']: raise ValueError('This is not the preferred original review packet')
        if any(not p.resolve().is_relative_to(review_public) for p in review_public.rglob('*')): raise ValueError('Review copy escapes its public folder')
        paired_url='preferred-review/review.html'
    if previous_page: previous_url='previous-explore.html'
    rat = next(b for b in books if b['id']=='rat')
    for chapter_index, paragraph, quiet in [(0,2,False),(1,0,True)]:
        chapter=rat['chapters'][chapter_index]
        scenes.append(dict(id='adventure-'+('reflection' if quiet else 'caper'),book={k:rat[k] for k in ('id','title','author','url','license')},chapter=chapter['title'],text=chapter['paragraphs'][paragraph],context='',adventureQuiet=quiet))
    data = dict(version=1, engineSha256=fingerprint, library=library, scenes=scenes, pairedUrl=paired_url, previousUrl=previous_url, readerUrl=reader_url, initialSet=initial_set, adventure=adventure, adventureSha256=hashlib.sha256((ROOT/'research/adventure-starting-score.json').read_bytes()).hexdigest())
    template = (ROOT / 'tools/exploration-review.html').read_text(encoding='utf-8')
    branching = (ROOT / 'tools/exploration-branching.cjs').read_text(encoding='utf-8')
    data['branchingVersion'] = 'awen-branching-1'
    data['branchingSha256'] = hashlib.sha256(branching.encode()).hexdigest()
    template = template.replace('__EXPLORATION_BRANCHING__', branching)
    template = template.replace('__ADVENTURE_RUNTIME__',(ROOT/'tools/adventure-explorer.cjs').read_text(encoding='utf8'))
    page = template.replace('__EXPLORATION_DATA__', json.dumps(data, ensure_ascii=False).replace('<', '\\u003c'))
    page = page.replace('__PRODUCTION_RUNTIME__', runtime)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    (output / 'explore.html').write_bytes(page.encode('utf-8'))
    if include_reader:
        (output / 'index.html').write_bytes((ROOT / 'index.html').read_bytes())
    if review_public: shutil.copytree(review_public,output/'preferred-review')
    if previous_page: (output/'previous-explore.html').write_bytes(Path(previous_page).read_bytes())
    manifest = dict(version=1, initialSet=initial_set, adventureSha256=data['adventureSha256'], reviewPacketSha256=adventure['reviewPacketSha256'], engineSha256=fingerprint, branchingVersion=data['branchingVersion'], branchingSha256=data['branchingSha256'], pageSha256=hashlib.sha256(page.encode()).hexdigest(),
                    createdAt=datetime.now(timezone.utc).isoformat(), scenes=[s['id'] for s in scenes],
                    readerIncluded=include_reader, readerSha256=hashlib.sha256((output / 'index.html').read_bytes()).hexdigest() if include_reader else None)
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    return output / 'explore.html'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, help='New output directory (never overwritten)')
    parser.add_argument('--paired-url', help='Optional link back to a separate paired review')
    parser.add_argument('--previous-url', help='Optional earlier explorer; keeps its sounds and backups available')
    parser.add_argument('--reader-url', help='Optional main reader link for the profile handoff')
    parser.add_argument('--include-reader', action='store_true', help='Also package the unchanged reader and link both pages')
    parser.add_argument('--initial-set',choices=['broad','bach','classical','adventure'],default='broad')
    parser.add_argument('--review-public',type=Path,help='Copy only the matching original review public folder')
    parser.add_argument('--previous-page',type=Path,help='Preserve an earlier frozen explorer beside the new page')
    args = parser.parse_args()
    output = args.output or ROOT / '.score-lab/exploration' / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex)
    print(build(output, args.paired_url, args.previous_url, args.reader_url, args.include_reader,args.initial_set,args.review_public,args.previous_page).resolve())
