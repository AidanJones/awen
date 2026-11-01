"""Small genuinely fitted regressors with RULE-GENERATED SYNTHETIC targets.

These exercise model storage/inference/replacement. They do not predict human
enjoyment or reading comfort. Standard library only; no pretrained weights.
"""
import array
import math
import random
import sys
import wave

VERSION = 'awen-synthetic-ridge-rewards-1'
FEATURES = ['rms', 'attack_density', 'zero_crossing', 'envelope_repetition',
            'envelope_variation', 'crest', 'difference_brightness']
AXES = ['fit', 'enjoyment', 'unobtrusiveness']


def bounded(x):
    return max(0., min(1., x))


def audio_features(file):
    with wave.open(str(file), 'rb') as wav:
        if (wav.getnchannels(), wav.getsampwidth(), wav.getframerate()) != (1, 2, 24000):
            raise ValueError('Expected native mono PCM16 24 kHz WAV')
        if not 240000 <= wav.getnframes() <= 24000 * 65:
            raise ValueError('Expected 10..65 seconds of bounded test audio')
        values = array.array('h'); values.frombytes(wav.readframes(wav.getnframes()))
    if sys.byteorder != 'little':
        values.byteswap()
    total = difference = block = 0.; peak = crossings = 0; previous = values[0]; envelope = []
    for i, value in enumerate(values):
        v = value / 32768.; old = previous / 32768.
        total += v*v; block += v*v; difference += (v-old)**2
        peak = max(peak, abs(v)); crossings += (value > 0) != (previous > 0)
        previous = value
        if (i+1) % 1200 == 0:
            envelope.append(math.sqrt(block/1200)); block = 0.
    rms = math.sqrt(total/len(values)); mean = sum(envelope)/len(envelope)
    variance = sum((v-mean)**2 for v in envelope)/len(envelope)
    attacks = sum(b > a*1.8 and b-a > .0007 for a, b in zip(envelope, envelope[1:]))
    lag = 40  # Fixed two-second amplitude-envelope repeat diagnostic, not musical quality.
    left, right = envelope[:-lag], envelope[lag:]
    ml, mr = sum(left)/len(left), sum(right)/len(right)
    norm = math.sqrt(sum((x-ml)**2 for x in left)*sum((x-mr)**2 for x in right))
    repeat = sum((a-ml)*(b-mr) for a,b in zip(left,right))/norm if norm > 1e-15 else 0.
    return [bounded(rms/.04), bounded(attacks/(len(values)/24000)/4),
            bounded(crossings/len(values)/.1), bounded(repeat),
            bounded(math.sqrt(variance)/(mean+1e-12)), bounded(peak/(rms+1e-12)/12),
            bounded(math.sqrt(difference/len(values))/(rms*.5+1e-12))]


def basis(features, density):
    if len(features) != len(FEATURES) or not all(type(v) in (int,float) and math.isfinite(v) and 0 <= v <= 1 for v in features):
        raise ValueError('Invalid reward feature vector')
    if type(density) not in (int,float) or not math.isfinite(density) or not 0 <= density <= 1:
        raise ValueError('Invalid synthetic context density')
    return [1., *features, *(v*v for v in features), density, density*density, features[1]*density]


def synthetic_targets(x, density):
    rms, attacks, zcr, repeat, variation, crest, bright = x
    return [bounded(1-(attacks-density)**2-.25*(bright-.35)**2),
            bounded(1-.5*(attacks-.35)**2-.3*(repeat-.35)**2-.2*(variation-.3)**2-.1*bright),
            bounded(1-.3*attacks-.25*bright-.15*zcr-.15*repeat-.15*rms)]


def solve(matrix, rhs):
    rows = [list(a)+[b] for a,b in zip(matrix,rhs)]; n=len(rows)
    for col in range(n):
        pivot=max(range(col,n),key=lambda r:abs(rows[r][col])); rows[col],rows[pivot]=rows[pivot],rows[col]
        if abs(rows[col][col]) < 1e-12:
            raise ValueError('Singular test-model fit')
        divisor=rows[col][col]; rows[col]=[v/divisor for v in rows[col]]
        for r in range(n):
            if r != col:
                factor=rows[r][col]; rows[r]=[a-factor*b for a,b in zip(rows[r],rows[col])]
    return [row[-1] for row in rows]


def train(seed=20261101, count=192):
    if type(count) is not int or not 32 <= count <= 1024:
        raise ValueError('Bounded synthetic training set required')
    rng=random.Random(seed); examples=[]
    for _ in range(count+48):
        x=[rng.random() for _ in FEATURES]; density=rng.random()
        examples.append({'features':x,'density':density,'targets':synthetic_targets(x,density)})
    weights={}
    for k,key in enumerate(AXES):
        rows=[basis(e['features'],e['density'] if key=='fit' else 0.) for e in examples[:count]]; n=len(rows[0])
        matrix=[[sum(r[i]*r[j] for r in rows)+(1e-3 if i==j and i else 0) for j in range(n)] for i in range(n)]
        weights[key]=solve(matrix,[sum(r[i]*e['targets'][k] for r,e in zip(rows,examples)) for i in range(n)])
    model={'version':VERSION,'testOnly':True,'labelSource':'rule-generated-synthetic',
           'personalComfortValidated':False,'features':FEATURES,'seed':seed,'trainingExamples':count,
           'weights':weights,'examples':examples}
    model['syntheticHoldoutMSE']={key:sum((predict(model,e['features'],e['density'])[key]-e['targets'][k])**2 for e in examples[count:])/48 for k,key in enumerate(AXES)}
    return model


def predict(model, features, density):
    if model.get('version') != VERSION or model.get('features') != FEATURES or model.get('testOnly') is not True:
        raise ValueError('Unsupported test model')
    basis(features,density); result={}
    for key in AXES:
        b=basis(features,density if key=='fit' else 0.)
        weights=model.get('weights',{}).get(key,[])
        if len(weights)!=len(b) or not all(type(v) in (int,float) and math.isfinite(v) for v in weights):
            raise ValueError('Invalid test-model weights')
        result[key]=bounded(sum(x*w for x,w in zip(b,weights)))
    return result


def pareto(rows):
    valid=[]
    for row in rows:
        if row.get('control') or not row.get('gate',{}).get('eligible'):
            continue
        if set(row.get('objectives',{}))!=set(AXES) or not all(type(v) in (int,float) and math.isfinite(v) for v in row['objectives'].values()):
            raise ValueError('Missing/nonfinite Pareto objective')
        valid.append(row)
    if len({r['card']['id'] for r in valid})!=len(valid):
        raise ValueError('Duplicate candidate identity')
    def dominates(a,b):
        return all(a[k]>=b[k] for k in AXES) and any(a[k]>b[k] for k in AXES)
    return sorted([r for r in valid if not any(dominates(other['objectives'],r['objectives']) for other in valid)],key=lambda r:r['card']['id'])


def parents(rows, count=2):
    front=pareto(rows)
    distance={r['card']['id']:0. for r in front}
    for axis in AXES:
        ordered=sorted(front,key=lambda r:(r['objectives'][axis],r['card']['id']))
        if not ordered:continue
        lo,hi=ordered[0]['objectives'][axis],ordered[-1]['objectives'][axis]
        if hi==lo:continue
        distance[ordered[0]['card']['id']]=distance[ordered[-1]['card']['id']]=float('inf')
        for i in range(1,len(ordered)-1):
            distance[ordered[i]['card']['id']]+=(ordered[i+1]['objectives'][axis]-ordered[i-1]['objectives'][axis])/(hi-lo)
    return sorted(front,key=lambda r:(-distance[r['card']['id']],r['card']['id']))[:count]
