"""Explicit pinned MuQ artifact preparation; offline verification is the default."""
import argparse
from pathlib import Path
import score_lab as lab
from muq_backend import verify_files, source_tree


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--download',action='store_true')
    parser.add_argument('--model-dir',type=Path,default=lab.ROOT/'.score-lab/muq-model')
    args=parser.parse_args();spec=lab.read(lab.ROOT/'research/muq-model.json')
    if args.download:
        from huggingface_hub import hf_hub_download
        groups=[('mulan',spec['modelId'],spec['revision']),
                ('audio','OpenMuQ/MuQ-large-msd-iter',spec['audioConfigRevision']),
                ('text','FacebookAI/xlm-roberta-base',spec['textConfigRevision'])]
        for sub,repo,revision in groups:
            for relative in spec['files']:
                prefix,name=relative.split('/',1)
                if prefix==sub:
                    hf_hub_download(repo,name,revision=revision,local_dir=args.model_dir/sub,token=False)
                    print('Cached',relative,flush=True)
    verify_files(args.model_dir,spec)
    if source_tree()!=spec['sourceTreeSha256']:raise ValueError('Installed source differs from pinned code')
    print('All pinned artifacts and installed MuQ source verified.')


if __name__=='__main__':main()
