import copy
from pathlib import Path
import tempfile
import unittest
import numpy as np
from video_workflow.common import fresh
from video_workflow.grade import curve, forward_hlg, inverse_hlg
from video_workflow.plan import compile_plan
from video_workflow.captions import srt
BASE={'profile':'sdr','width':180,'height':320,'fps':20,'audio_overlap':.2,
      'scenes':[{'file':'a.mov','in':1,'out':4},{'file':'b.mov','in':0,'out':3},{'file':'c.mov','in':0,'out':3}],
      'transitions':[{'type':'fadeblack','duration':.4},{'type':'rollright','duration':.4}], 'captions':[]}
class WorkflowTests(unittest.TestCase):
    def test_timeline_preserves_exact_frames(self):
        p=compile_plan(BASE,Path('/tmp'))
        self.assertEqual(sum(s['body_end']-s['body_start'] for s in p['scenes'])+sum(t['frames'] for t in p['transitions']),p['frames'])
        self.assertEqual(p['frames'],172)
    def test_reject_overlapping_captions(self):
        raw=copy.deepcopy(BASE)
        raw['captions']=[{'start':1,'end':2,'text':'uno'},{'start':1.5,'end':3,'text':'dos'}]
        with self.assertRaises(ValueError):compile_plan(raw,Path('/tmp'))
    def test_reject_short_transition_handle(self):
        raw=copy.deepcopy(BASE);raw['scenes'][1]['out']=.3
        with self.assertRaises(ValueError):compile_plan(raw,Path('/tmp'))
    def test_reject_broll_outside_scene(self):
        raw=copy.deepcopy(BASE);raw['scenes'][0]['broll']=[{'file':'d.mov','in':0,'at':2.8,'duration':1}]
        with self.assertRaises(ValueError):compile_plan(raw,Path('/tmp'))
    def test_existing_output_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/'original.mov';f.write_text('original')
            with self.assertRaises(ValueError):fresh(f)
            self.assertEqual(f.read_text(),'original')
    def test_hlg_round_trip_and_curves(self):
        x=np.linspace(0,1,100)
        np.testing.assert_allclose(forward_hlg(inverse_hlg(x)),x,atol=1e-7)
        for c in curve(np.array([.1,-.1,0,-.2,.025])):
            ys=[float(pair.split('/')[1]) for pair in c.split()]
            self.assertTrue(np.all(np.diff(ys)>=0));self.assertEqual((ys[0],ys[-1]),(0,1))
    def test_srt_timing(self):
        self.assertIn('00:00:01,250 --> 00:00:02,000',srt([{'start':1.25,'end':2,'text':'Hola'}]))
if __name__=='__main__':unittest.main()
