"""Real FFmpeg smoke test; all media generated locally and gitignored."""
import argparse
from pathlib import Path
import tempfile
from video_workflow.common import digest, encoder, ff, verify, write_json, profile_filter
from video_workflow.render import render
from video_workflow.captions import burn
from video_workflow.grade import grade
parser=argparse.ArgumentParser()
parser.add_argument('--font',required=True)
parser.add_argument('--profile',choices=['sdr','hlg'],default='sdr')
args=parser.parse_args()
with tempfile.TemporaryDirectory(prefix='workflow-smoke-',dir='outputs') as td:
    root=Path(td).resolve();fps=20;hdr=args.profile=='hlg';files=[]
    for i,color in enumerate(('gray','silver','gray')):
        file=root/f'{i}.mov'
        ff(['-f','lavfi','-i',f'color=c={color}:s=180x320:r={fps}:d=3','-f','lavfi','-i',f'sine=frequency={400+i*100}:sample_rate=48000:duration=3','-vf',profile_filter(args.profile),*encoder(args.profile,'software','1M',fps),'-c:a','pcm_s16le',str(file)],root/f'{i}.log');files.append(file)
    original={str(f):digest(f) for f in files}
    plan=dict(profile=args.profile,width=180,height=320,fps=fps,bitrate='1M',audio_overlap=.2,audio_filter='',
              scenes=[dict(file=str(f),title=f'Scene {i}',**{'in':.2,'out':2.8},broll=[dict(file=str(files[1]),**{'in':.1},at=.8,duration=.6,fade=.1)] if i==0 else []) for i,f in enumerate(files)],
              transitions=[dict(type='fadeblack',duration=.4),dict(type='rollright',duration=.4)],captions=[])
    write_json(root/'plan.json',plan);master=render(root/'plan.json',root/'render');verify(master,180,320,fps,args.profile,7.4);source=master
    if hdr:
        write_json(root/'samples.json',dict(edit_plan='plan.json',reference=dict(seconds=6,scene=2,roi=[.1,.1,.9,.9]),samples=[dict(seconds=.5,scene=0,roi=[.1,.1,.9,.9]),dict(seconds=1.1,scene=0,broll=0,roi=[.1,.1,.9,.9]),dict(seconds=4,scene=1,roi=[.1,.1,.9,.9])]))
        source=root/'graded.mov';grade(master,root/'samples.json',source,bitrate='1M')
    write_json(root/'caps.json',[dict(start=.5,end=1.2,text='Hola'),dict(start=5,end=6,text='Otro plano')])
    burn(source,root/'caps.json',root/'captioned.mp4',args.font,bitrate='1M');verify(root/'captioned.mp4',180,320,fps,args.profile,7.4)
    ff(['-v','error','-xerror','-i',str(root/'captioned.mp4'),'-f','null','-'],root/'decode.log')
    assert original=={str(f):digest(f) for f in files}
    print(f'PASS: {args.profile}, montage, B-roll, transitions, audio, captions, decode, originals'+(', color match' if hdr else ''))
