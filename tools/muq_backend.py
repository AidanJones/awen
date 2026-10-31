"""Pinned local MuQ-MuLan inference, isolated from the existing CLAP environment."""
import hashlib
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path

from clap_backend import normalized

PACKAGES = ['torch','torchaudio','transformers','numpy','scipy','tokenizers','huggingface-hub',
            'muq','einops','nnAudio','easydict','x-clip','sentencepiece','librosa']


def source_tree():
    spec = importlib.util.find_spec('muq')
    if spec is None: raise RuntimeError('Install the isolated MuQ environment first')
    root = Path(spec.origin).parent
    files = {'muq/'+p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
             for p in root.rglob('*.py')}
    return hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest()


def identity(spec):
    tree = source_tree()
    if tree!=spec['sourceTreeSha256']: raise ValueError('Installed MuQ source does not match pinned commit')
    return dict(spec=spec, packages={p:importlib.metadata.version(p) for p in PACKAGES},
                backendSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), sourceTreeSha256=tree)


def verify_files(root, spec):
    for relative, expected in spec['files'].items():
        file = Path(root)/relative
        if file.stat().st_size!=expected['bytes']: raise ValueError('Wrong artifact size: '+relative)
        digest = hashlib.sha256()
        with file.open('rb') as stream:
            for block in iter(lambda:stream.read(8*1024*1024),b''): digest.update(block)
        if digest.hexdigest()!=expected['sha256']: raise ValueError('Wrong artifact checksum: '+relative)


class MuQBackend:
    def __init__(self, spec, model_cache, download=False):
        if download: raise ValueError('Use pinned preflight downloads; inference is offline only')
        os.environ['HF_HUB_OFFLINE']='1'
        os.environ['TRANSFORMERS_OFFLINE']='1'
        os.environ['HF_HUB_DISABLE_TELEMETRY']='1'
        import numpy as np
        import torch
        from unittest.mock import patch
        from transformers import XLMRobertaConfig, XLMRobertaModel, AutoTokenizer
        from muq import MuQ, MuQMuLan
        from muq.muq_mulan.models.audio import AudioSpectrogramTransformerPretrained
        from muq.muq_mulan.models.text import TextTransformerPretrained
        self.spec,self.np,self.torch=spec,np,torch
        if source_tree()!=spec['sourceTreeSha256']: raise ValueError('MuQ code identity changed')
        root=Path(model_cache)
        verify_files(root,spec)
        prep=spec['preprocessing']
        np.random.seed(prep['seed']);torch.manual_seed(prep['seed'])
        torch.set_num_threads(prep['threads']);torch.use_deterministic_algorithms(True)
        read=lambda path:json.loads((root/path).read_text(encoding='utf8'))
        audio_config=read('audio/config.json')
        config=read('mulan/config.json')
        if config['mulan']['sr']!=24000 or config['mulan']['clip_secs']!=10 or config['mulan']['dim_latent']!=512:
            raise ValueError('Unexpected MuLan audio/projection config')
        if audio_config['is_flash']: raise ValueError('This CPU backend requires the non-flash model')
        def audio_init(module, name):
            if name!='OpenMuQ/MuQ-large-msd-iter': raise ValueError('Unexpected audio architecture')
            module.model=MuQ(audio_config)
        def text_init(module):
            if module.model_name!='xlm-roberta-base': raise ValueError('Unexpected text architecture')
            return XLMRobertaModel(XLMRobertaConfig.from_json_file(root/'text/config.json'))
        # The released full state includes both base networks. Instantiate their architectures
        # locally instead of downloading redundant base weights, then require a complete load.
        with patch.object(AudioSpectrogramTransformerPretrained,'_init_pretrained_model',audio_init), \
             patch.object(TextTransformerPretrained,'_init_pretrained_model',text_init):
            self.model=MuQMuLan(config)
        state=torch.load(root/'mulan/pytorch_model.bin',map_location='cpu',weights_only=True,mmap=True)
        result=self.model.load_state_dict(state,strict=True,assign=True)
        if result.missing_keys or result.unexpected_keys: raise ValueError('Incomplete model state')
        self.state_keys=len(state)
        self.model=self.model.to(device='cpu',dtype=torch.float32).requires_grad_(False).eval()
        self.tokenizer=AutoTokenizer.from_pretrained(root/'text',local_files_only=True,use_fast=True)
        self.model.mulan.text._tokenizer=self.tokenizer
        print('MuQ complete strict state load:',self.state_keys,'keys; offline CPU float32',flush=True)

    def feature(self, kind, payload, pcm=None):
        torch,np=self.torch,self.np
        with torch.inference_mode():
            if kind=='text':
                if len(self.tokenizer(payload['text'],truncation=False)['input_ids'])>510:
                    raise ValueError('Text exceeds pinned XLM-R token budget')
                vector=self.model(texts=[payload['text']])[0]
            elif kind=='audio':
                samples=np.frombuffer(pcm,dtype='<i2').astype(np.float32)/32768
                if len(samples)!=240000: raise ValueError('Expected exact ten-second 24 kHz PCM window')
                vector=self.model(wavs=torch.from_numpy(samples).unsqueeze(0),parallel_processing=False)[0]
            else: raise ValueError('Unknown feature kind')
        return normalized(vector.cpu().float().tolist(),self.spec['dimension'])
