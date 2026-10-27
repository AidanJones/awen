"""TEST ONLY score matrices, with no invented preference labels."""
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import compare_evaluators as comparison


class ComparisonTests(unittest.TestCase):
    def test_selection_changes_with_objective_and_respects_gates(self):
        def row(id,a,b,contrast,eligible=True):
            return {'card':{'id':id},'gate':{'eligible':eligible},'scores':[{'target-1':a,'target-2':b,'contrast':contrast}]*2}
        rows=[row('a',.9,.3,.8),row('b',.4,.6,.1),row('invalid',1,1,0,False)]
        self.assertEqual(comparison.choose(rows,'single-1')['card']['id'],'a')
        self.assertEqual(comparison.choose(rows,'single-2')['card']['id'],'b')
        self.assertEqual(comparison.choose(rows,'ensemble')['card']['id'],'a')
        self.assertEqual(comparison.choose(rows,'contrastive')['card']['id'],'b')
        rows[0]['scores'][0]['new-1']=1000
        self.assertEqual(comparison.choose(rows,'contrastive')['card']['id'],'b')

    def test_exact_ties_have_stable_identity_order(self):
        rows=[{'card':{'id':key},'gate':{'eligible':True},'scores':[{'target-1':.2,'target-2':.3,'contrast':.1}]} for key in ['z','a']]
        self.assertEqual(comparison.choose(rows,'ensemble')['card']['id'],'a')


if __name__=='__main__': unittest.main()
