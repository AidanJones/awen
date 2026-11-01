"""Engineering tests. Fake encoders/audio and synthetic labels are not listening evidence."""
import copy
import io
import math
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import wave

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import multiobjective_lab as mo
import reward_test_models as models
import score_lab as lab


def row(id, values, eligible=True, control=None):
    return dict(card={'id':id},objectives=dict(zip(models.AXES,values)),gate={'eligible':eligible},control=control)


class FakeEngine(mo.Engine):
    calls=0
    def worker(self,command,input_path,output_path,log_path):
        payload=lab.read(input_path)
        if command=='test-reward':return super().worker(command,input_path,output_path,log_path)
        type(self).calls+=1
        if command=='grid-plan':
            result=dict(cards=[dict(id=id,name=id,genome={'TEST_ONLY':id},palette='ensemble') for id in self.manifest['suite']['cardIds']],
                        scenes=[dict(id=s['id'],text='TEST ONLY passage',book={'id':s['book'],'title':'TEST ONLY','url':'https://example.invalid'}) if (s:=next((s for s in self.manifest['suite']['scenes'] if s['index']==i),None)) else {} for i in range(5)])
        elif command=='grid-children':
            result=[dict(payload['parents'][i%len(payload['parents'])],id=payload['parents'][i%len(payload['parents'])]['id']+'-child-'+str(i),parentId=payload['parents'][i%len(payload['parents'])]['id']) for i in range(payload['count'])]
        elif command=='render':
            folder=output_path.parent; data=io.BytesIO()
            # A repeated small PCM cycle is sufficient to test storage/feature plumbing.
            import array
            pcm=array.array('h',(int(500*math.sin(2*math.pi*i/120)) for i in range(24000)))
            if sys.byteorder!='little':pcm.byteswap()
            with wave.open(data,'wb') as wav:wav.setparams((1,2,24000,0,'NONE','not compressed'));wav.writeframes(pcm.tobytes()*32)
            lab.atomic(folder/'audio.wav',data.getvalue());lab.atomic(folder/'trace.json',b'{"TEST_ONLY":true}\n')
            result=dict(file='audio.wav',sha256=lab.sha(data.getvalue()),traceFile='trace.json',traceSha256=lab.sha((folder/'trace.json').read_bytes()),signal={'rms':.01,'peak':.02},structure={'TEST_ONLY':True},gate={'eligible':True,'reasons':[]},renderer={'TEST_ONLY':'fake'})
        else:raise ValueError(command)
        lab.atomic(log_path,b'TEST ONLY fake native worker\n',exclusive=True)
        lab.atomic(output_path,lab.encode(dict(requestSha256=lab.sha(input_path.read_bytes()),result=result)))


class ModelsTests(unittest.TestCase):
    def test_fitted_models_are_deterministic_and_explicitly_synthetic(self):
        model=models.train();self.assertEqual(model,models.train());self.assertTrue(model['testOnly']);self.assertEqual(model['labelSource'],'rule-generated-synthetic')
        self.assertTrue(all(v<.001 for v in model['syntheticHoldoutMSE'].values()))
        x=[.3]*7;a=models.predict(model,x,0.);b=models.predict(model,x,1.)
        self.assertEqual(a['enjoyment'],b['enjoyment']);self.assertEqual(a['unobtrusiveness'],b['unobtrusiveness']);self.assertNotEqual(a['fit'],b['fit'])
        for bad in [[float('nan')]*7,[True]*7,[-1.]*7,[0.]*6]:
            with self.assertRaises(ValueError):models.predict(model,bad,.5)
        wrong=copy.deepcopy(model);wrong['weights']['fit'][0]=float('inf')
        with self.assertRaises(ValueError):models.predict(wrong,x,.5)

    def test_pareto_preserves_tradeoffs_ties_and_excludes_controls_before_ranking(self):
        rows=[row('a',[1,0,0]),row('b',[0,1,1]),row('dominated',[0,0,0]),row('same-a',[1,0,0]),row('invalid',[999,999,999],False),row('control',[999,999,999],control='silence')]
        self.assertEqual([r['card']['id'] for r in models.pareto(rows)],['a','b','same-a'])
        changed=copy.deepcopy(rows)
        for r in changed:r['objectives']['fit']=r['objectives']['fit']*100-20
        self.assertEqual([r['card']['id'] for r in models.pareto(rows)],[r['card']['id'] for r in models.pareto(changed)])
        self.assertEqual(len(models.parents(rows)),2)
        with self.assertRaises(ValueError):models.pareto([row('bad',[float('nan'),1,1])])
        with self.assertRaises(ValueError):models.pareto([rows[0],rows[0]])


class RecoveryTests(unittest.TestCase):
    def test_pause_zero_budget_resume_and_complete_replay(self):
        root=mo.ROOT/'.score-lab/tests';root.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=root) as tmp:
            directory=mo.create(tmp);log=lab.Invocation(directory)
            try:
                with patch('builtins.print'):
                    with self.assertRaises(lab.Paused):FakeEngine(directory,log,2,0).drive()
                    before=lab.read(directory/'state.json');count=FakeEngine.calls
                    with self.assertRaises(lab.Paused):FakeEngine(directory,log,0,0).drive()
                    self.assertEqual(FakeEngine.calls,count)
                    report=FakeEngine(directory,log).drive()
                    self.assertTrue(report['testOnly']);self.assertFalse(report['promotionAllowed']);self.assertEqual(report['humanRatings'],0)
                    self.assertEqual(len(report['scenes']),3)
                    for group in report['scenes']:
                        self.assertEqual(len(group['initial']),4);self.assertEqual(len(group['children']),2);self.assertEqual(len(group['controls']),3)
                        self.assertFalse(any(id.startswith('control') for id in group['paretoIds']))
                    count=FakeEngine.calls;state=lab.read(directory/'state.json');again=FakeEngine(directory,log,0,0).drive()
                    self.assertEqual(report,again);self.assertEqual(FakeEngine.calls,count)
                    self.assertEqual(len(state['jobs']),len(lab.read(directory/'state.json')['jobs']))
                    self.assertTrue(all(len(j['attempts'])==1 for j in state['jobs'].values()))
                    features=next((directory/'audio-features').glob('*.json'));original=features.read_bytes();features.write_text('{}')
                    with self.assertRaises(ValueError):FakeEngine(directory,log).drive()
                    features.write_bytes(original)
                    # Every resumed artifact is verified, including PCM and model weights.
                    job=next(j for j in state['jobs'].values() if j['kind']=='render');file=directory/job['result'];wav=file.parent/'audio.wav';wav.write_bytes(wav.read_bytes()+b'corrupt')
                    with self.assertRaises(ValueError):FakeEngine(directory,log).drive()
            finally:log.close()

    def test_published_artifact_recovers_without_a_second_execution(self):
        root=mo.ROOT/'.score-lab/tests';root.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=root) as tmp:
            directory=mo.create(tmp);log=lab.Invocation(directory)
            try:
                engine=FakeEngine(directory,log)
                def crash(stage,key):
                    if stage=='after_result_publish':raise KeyboardInterrupt('TEST ONLY crash')
                engine.fault_hook=crash
                request=dict(page=str(engine.page),startingSet='classical')
                with self.assertRaises(KeyboardInterrupt):engine.execute('grid-plan',request)
                count=FakeEngine.calls;engine=FakeEngine(directory,log,0,0);engine.execute('grid-plan',request)
                self.assertEqual(FakeEngine.calls,count)
                model=directory/'test-models.json';model.write_bytes(model.read_bytes()+b' ')
                with self.assertRaises(ValueError):FakeEngine(directory,log)
            finally:log.close()

    def test_reward_result_contract_rejects_missing_nan_and_wrong_identity(self):
        good={'modelSha256':'a','testOnly':True,'objectives':dict(fit=.1,enjoyment=.2,unobtrusiveness=.3)}
        mo.validate_prediction(good,'a')
        for bad in [{**good,'modelSha256':'b'},{**good,'testOnly':False},{**good,'objectives':{'fit':.1}},{**good,'objectives':dict(good['objectives'],fit=float('nan'))}]:
            with self.assertRaises(ValueError):mo.validate_prediction(bad,'a')

    def test_failed_local_job_gets_a_unique_new_attempt(self):
        root=mo.ROOT/'.score-lab/tests';root.mkdir(parents=True,exist_ok=True)
        class FailOnce(FakeEngine):
            fail=True
            def worker(self,*args):
                if self.fail:
                    self.fail=False
                    raise RuntimeError('TEST ONLY local worker failure')
                return super().worker(*args)
        with tempfile.TemporaryDirectory(dir=root) as tmp:
            directory=mo.create(tmp);log=lab.Invocation(directory)
            try:
                engine=FailOnce(directory,log);request=dict(page=str(engine.page),startingSet='classical')
                with self.assertRaises(RuntimeError):engine.execute('grid-plan',request)
                engine.execute('grid-plan',request)
                job=next(iter(lab.read(directory/'state.json')['jobs'].values()))
                self.assertEqual([a['status'] for a in job['attempts']],['failed','complete'])
                self.assertNotEqual(job['attempts'][0]['directory'],job['attempts'][1]['directory'])
                self.assertTrue((directory/job['attempts'][0]['directory']/'failure.txt').exists())
            finally:log.close()


if __name__=='__main__':unittest.main()
