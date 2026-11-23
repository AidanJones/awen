"""Small resumable adventure-arrangement comparison; no automatic musical winner."""
import argparse
import array
import io
from pathlib import Path
import random
import subprocess
import sys
import uuid
import wave

import score_lab as lab
import recurrence_listening as recurrence

VERSION = 'awen-adventure-pilot-1'
TREATMENTS = ['baseline', 'arranged']
SOURCES = ['index.html', 'tools/adventure_listening.py', 'tools/adventure-worker.cjs',
           'tools/adventure-arrangement.cjs', 'tools/score_lab.py', 'tools/score-lab.cjs',
           'tools/score-lab-metrics.cjs', 'tools/recurrence_listening.py',
           'tools/recurrence-review.html', 'tools/recurrence_ratings.py']


def sources():
    return {p: lab.sha((lab.ROOT/p).read_bytes()) for p in SOURCES}


def create(root):
    directory = Path(root).resolve()/(lab.stamp()+'-'+uuid.uuid4().hex)
    directory.mkdir(parents=True)
    manifest = dict(version=VERSION, id=uuid.uuid4().hex, createdAt=lab.now(),
                    sources=sources(), seed='adventure-pilot-1', steps=384,
                    treatments=TREATMENTS, palette='romantic', humanRatings=0,
                    scope='Two fixed passages, one palette, three 16-bar cycles; static arrangement, not adaptive transitions.')
    raw = lab.encode(manifest)
    lab.atomic(directory/'experiment.json', raw, exclusive=True)
    lab.atomic(directory/'state.json', lab.encode(dict(manifestSha256=lab.sha(raw),
               status='created', jobs={}, renderer=None)), exclusive=True)
    return directory


def read_pcm(raw):
    with wave.open(io.BytesIO(raw), 'rb') as reader:
        if (reader.getnchannels(), reader.getsampwidth(), reader.getframerate()) != (1, 2, 24000):
            raise ValueError('Expected native mono 24 kHz PCM16')
        samples = array.array('h', reader.readframes(reader.getnframes()))
    if sys.byteorder != 'little':
        samples.byteswap()
    rms = (sum(v*v for v in samples)/len(samples))**.5/32767
    if not rms > .0001:
        raise ValueError('Silent recording')
    return samples, rms


def attenuate(samples, gain):
    if not 0 < gain <= 1:
        raise ValueError('Only attenuation is permitted')
    output = array.array('h', (round(v*gain) for v in samples))
    rms = (sum(v*v for v in output)/len(output))**.5/32767
    peak = max(abs(v) for v in output)/32767
    if sys.byteorder != 'little':
        output.byteswap()
    stream = io.BytesIO()
    with wave.open(stream, 'wb') as writer:
        writer.setnchannels(1); writer.setsampwidth(2); writer.setframerate(24000)
        writer.writeframes(output.tobytes())
    return stream.getvalue(), rms, peak


class Engine(recurrence.Engine):
    def __init__(self, directory, log, max_new_renders=None):
        self.directory = Path(directory).resolve()
        self.manifest, self.state = [lab.read(self.directory/p) for p in ['experiment.json', 'state.json']]
        if (self.manifest['version'] != VERSION or self.manifest['sources'] != sources()
            or self.state['manifestSha256'] != lab.sha((self.directory/'experiment.json').read_bytes())):
            raise ValueError('Experiment/source identity changed; start a fresh run')
        self.log, self.retry, self.fault_hook = log, set(), lambda *_: None
        self.max_new_renders, self.new_renders = max_new_renders, 0

    def worker(self, command, input_path, output_path, log_path):
        with Path(log_path).open('xb') as stream:
            process = subprocess.Popen(['node', str(lab.ROOT/'tools/adventure-worker.cjs'),
                command, str(input_path), str(output_path)], cwd=lab.ROOT, stdout=stream, stderr=subprocess.STDOUT)
            try:
                code = process.wait()
            except BaseException:
                process.terminate(); process.wait(); raise
            if code:
                raise RuntimeError(f'Native worker exited {code}; see {log_path}')

    def drive(self):
        self.state['status'] = 'running'; self.save()
        scenes = self.execute('plan', {})
        clips, measures = {}, []
        for scene in scenes:
            pair = []
            for treatment in TREATMENTS:
                payload = dict(scene=scene, treatment=treatment, seed=self.manifest['seed'])
                result = self.execute('render', payload)
                _, job = self.ensure_job('render', payload)
                source = lab.safe(self.directory, job['result']).parent/result['file']
                samples, rms = read_pcm(source.read_bytes())
                pair.append((treatment, result, samples, rms))
            target = min(.018, *(row[3] for row in pair))
            for treatment, result, samples, rms in pair:
                gain = target/rms
                wav, matched_rms, peak = attenuate(samples, gain)
                if abs(matched_rms-target) > 2/32767 or peak > result['cap']+2/32767:
                    raise ValueError('Matched signal check failed')
                name = 'audio/'+lab.sha(wav)[:24]+'.wav'
                lab.atomic(self.directory/'public'/name, wav, exclusive=True)
                clips[scene['id'], treatment] = dict(file=name, sha256=lab.sha(wav), seconds=result['seconds'])
                measures.append(dict(scene=scene['id'], treatment=treatment,
                    raw=result, targetRms=target, matchedRms=matched_rms, matchedPeak=peak, gain=gain,
                    publishedSha256=lab.sha(wav)))
        packet, key = make_packet(self.manifest, scenes, clips)
        raw = lab.encode(packet); packet_sha = lab.sha(raw)
        template = (lab.ROOT/'tools/recurrence-review.html').read_text(encoding='utf8')
        template = template.replace('Recurring figures review', 'Adventure arrangement review').replace(
            'Which recurring accompaniment works while reading?', 'Which arrangement works while reading?')
        template = template.replace('excerpts are 86 seconds.', 'excerpts are 165 seconds.')
        embedded = lab.encode(dict(packet=packet, packetSha256=packet_sha)).decode().replace('<', '\\u003c')
        lab.atomic(self.directory/'private-key.json', lab.encode(key), exclusive=True)
        lab.atomic(self.directory/'packet.json', raw, exclusive=True)
        lab.atomic(self.directory/'public/review.html', template.replace('__CALIBRATION_DATA__', embedded).encode(), exclusive=True)
        report = dict(version=VERSION, packetSha256=packet_sha, privateKeySha256=lab.sha(lab.encode(key)),
            clips=len(clips), trials=len(packet['trials']), measures=measures, humanRatings=0,
            thresholdChanged=False, promotionAllowed=False,
            levelMatching='Paired whole-clip RMS, attenuation only; not perceptual loudness matching.',
            limits='One seed/palette, two authored passage choices. No timbre realism, reading benefit or musical winner established.')
        lab.atomic(self.directory/'report.json', lab.encode(report), exclusive=True)
        self.state['status'] = 'awaiting-listener'; self.save()
        return report


def make_packet(manifest, scenes, clips):
    rng = random.Random(manifest['seed']); trials, key = [], {}
    for scene in scenes:
        a, b = TREATMENTS
        if rng.randrange(2): a, b = b, a
        first = uuid.uuid5(uuid.NAMESPACE_URL, manifest['id']+scene['id']).hex
        for repeat in [False, True]:
            ident = first if not repeat else uuid.uuid5(uuid.NAMESPACE_URL, first+'repeat').hex
            x, y = (a, b) if not repeat else (b, a)
            trials.append(dict(id=ident, scene=scene['id'], A=clips[scene['id'], x], B=clips[scene['id'], y]))
            key[ident] = dict(scene=scene['id'], A=x, B=y, repeatOf=first if repeat else None)
    rng.shuffle(trials)
    return dict(id=manifest['id'], version=VERSION,
        instructions='Compare while reading. Each clip lasts 165 seconds: three 16-bar cycles plus a tail. Fit, enjoyment and distraction are separate questions. Reversed repeats are optional consistency checks, not correct-answer tests. You may skip, pause or stop; download a ratings backup to continue later.',
        scenes=[{k:v for k,v in s.items() if k not in ['genome', 'palette']} for s in scenes], trials=trials), key


def run(directory, max_new_renders=None, fault_hook=None):
    directory = Path(directory).resolve()
    with lab.RunLock(directory):
        log = lab.Invocation(directory)
        try:
            engine = Engine(directory, log, max_new_renders)
            if fault_hook: engine.fault_hook = fault_hook
            report = engine.drive(); log.event('prepared', clips=report['clips'], humanRatings=0)
            return report
        except BaseException as error:
            log.event('stopped', exception=type(error).__name__); raise
        finally: log.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['start', 'resume'])
    parser.add_argument('directory', nargs='?', type=Path)
    parser.add_argument('--root', type=Path, default=lab.ROOT/'.score-lab/adventure-listening')
    parser.add_argument('--max-new-renders', type=int)
    args = parser.parse_args()
    if args.command == 'resume' and not args.directory: parser.error('Resume needs a directory')
    if args.max_new_renders is not None and args.max_new_renders < 0: parser.error('Render budget must be nonnegative')
    directory = create(args.root) if args.command == 'start' else args.directory.resolve()
    print('Experiment:', directory, flush=True)
    try:
        result = run(directory, args.max_new_renders)
        print(dict(status='awaiting-listener', clips=result['clips'], trials=result['trials']))
    except lab.Paused as error: print('Paused:', error)
