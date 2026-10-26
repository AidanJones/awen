"""Validate and embed the small scoring library. Maintenance only; no app build required."""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATTERN = r'<!-- SCORING_KNOWLEDGE_START -->[\s\S]*?<!-- SCORING_KNOWLEDGE_END -->'


def validate(data):
    assert data['schemaVersion'] == 1 and data['id'] == 'awen-scoring-knowledge'
    assert re.fullmatch(r'\d+\.\d+\.\d+', data['version'])
    sources = {s['id'] for s in data['sources']}
    assert len(sources) == len(data['sources'])
    assert all(s['url'].startswith('https://') and s['reviewed'] for s in data['sources'])
    families = {f['id'] for f in data['harmonicFamilies']}
    assert len(families) == len(data['harmonicFamilies'])
    for family in data['harmonicFamilies']:
        assert family['evidenceStatus'] == 'awen-proposal' and family['sourceScope']
        assert set(family['sourceIds']) <= sources and family['sourceIds']
        assert family['harmonicBars'] in (1, 2, 4) and len(family['chords']) == 4
        assert 4 <= len(family['form']) <= 16
        assert all(type(i) is int and 0 <= i < 4 for i in family['form'])
        for chord in family['chords']:
            assert type(chord['root']) is int and 0 <= chord['root'] < 12
            assert len(chord['intervals']) == len(set(chord['intervals'])) == 4
            assert 0 in chord['intervals']
            assert all(type(n) is int and 0 <= n < 12 for n in chord['intervals'])
    for genre in data['genres'].values():
        assert genre['evidenceStatus'] == 'awen-proposal'
        assert set(genre['sourceIds']) <= sources
        assert set(genre['sceneChoices']) == set(data['sceneFunctions'])
        for choices in genre['sceneChoices'].values():
            assert choices and set(choices) <= families
    for item in list(data['principles']) + list(data['sceneFunctions'].values()):
        assert set(item['sourceIds']) <= sources
    assert set(data['sceneAliases'].values()) <= set(data['sceneFunctions'])
    assert set(data['genreAliases'].values()) <= set(data['genres'])
    assert data['constraints']['voices'] == 4
    assert data['constraints']['midiMin'] == 55 and data['constraints']['midiMax'] == 79
    assert data['constraints']['minVoiceGap'] == 3
    assert data['constraints']['transition'] == 'four-bar-phrase'
    assert data['constraints']['exactProgressionsAreOriginal'] is True
    assert data['constraints']['readingBenefitEstablished'] is False
    assert data['constraints']['automaticSceneSelection'] is False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Verify the embedded copy without writing')
    args = parser.parse_args()
    data = json.loads((ROOT / 'research/scoring-knowledge.json').read_text(encoding='utf-8'))
    validate(data)
    path = ROOT / 'index.html'
    html = path.read_text(encoding='utf-8')
    payload = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')
    block = '<!-- SCORING_KNOWLEDGE_START -->\n<script id="scoring-knowledge" type="application/json">' + payload + '</script>\n<!-- SCORING_KNOWLEDGE_END -->'
    if args.check:
        match = re.search(r'<script id="scoring-knowledge" type="application/json">(.*?)</script>', html, re.S)
        assert match and json.loads(match[1]) == data, 'Embedded scoring library is stale; run this script without --check'
        print('Scoring library validated; embedded copy matches.')
        return
    if re.search(PATTERN, html):
        html = re.sub(PATTERN, lambda _: block, html)
    else:
        marker = "<script>\n'use strict';"
        assert marker in html
        html = html.replace(marker, block + '\n' + marker, 1)
    path.write_text(html, encoding='utf-8')
    print('Scoring library validated and embedded.')


if __name__ == '__main__':
    main()
