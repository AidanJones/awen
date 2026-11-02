"""Download pinned Audiobox files explicitly; otherwise verify local files offline."""
import argparse
from pathlib import Path
import urllib.request

import score_lab as lab
from audiobox_backend import verify_files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--download', action='store_true')
    parser.add_argument('--root', type=Path, default=lab.ROOT / '.score-lab/audiobox-preflight')
    args = parser.parse_args()
    spec = lab.read(lab.ROOT / 'research/audiobox-model.json')
    if args.download:
        from huggingface_hub import hf_hub_download
        for name, expected in spec['files'].items():
            file = lab.safe(args.root, name)
            if file.is_file() and file.stat().st_size == expected['bytes']:
                continue  # Full checksums verified below; never silently accept corruption.
            if name.startswith('model/'):
                hf_hub_download(spec['modelId'], name.split('/', 1)[1], revision=spec['revision'], local_dir=args.root / 'model', token=False)
            else:
                url = ('https://huggingface.co/'+spec['modelId']+'/resolve/'+spec['revision']+'/'+name) if name == 'config.json' else (
                    'https://raw.githubusercontent.com/facebookresearch/audiobox-aesthetics/'+spec['sourceRevision']+'/'+name.removeprefix('source/'))
                data = urllib.request.urlopen(url, timeout=60).read()
                if len(data) != expected['bytes'] or lab.sha(data) != expected['sha256']:
                    raise ValueError('Downloaded source/config checksum mismatch')
                lab.atomic(file, data, exclusive=True)
            print('Cached', name, flush=True)
    verify_files(args.root, spec)
    print('All pinned weights, configuration, source and licence files verified.')


if __name__ == '__main__':
    main()
