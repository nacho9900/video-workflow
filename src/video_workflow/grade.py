"""Restrained HLG neutral matching. Explicit ROIs; no automatic artistic judgement."""
import json
import math
from pathlib import Path
import subprocess
import numpy as np
from .common import binary, encoder, ff, fresh, verify, video, write_json, verify_audio_copy
from .plan import load_plan

A=.17883277
B=1-4*A
C=.5-A*math.log(4*A)


def inverse_hlg(x):
    x=np.asarray(x)
    return np.where(x<=.5,x*x/3,(np.exp((x-C)/A)+B)/12)


def forward_hlg(x):
    x=np.maximum(x,0)
    return np.where(x<=1/12,np.sqrt(3*x),A*np.log(np.maximum(12*x-B,1e-12))+C)


def sample(source, seconds, roi):
    raw=subprocess.check_output([binary('ffmpeg'),'-v','error','-ss',str(seconds),'-i',str(source),'-vf','scale=180:320:flags=area,format=rgb48le','-frames:v','1','-f','rawvideo','-'])
    image=np.frombuffer(raw,dtype='<u2').reshape(320,180,3)/65535
    x0,y0,x1,y1=roi
    if not 0<=x0<x1<=1 or not 0<=y0<y1<=1:
        raise ValueError('ROI uses normalized x0,y0,x1,y1 coordinates')
    crop=image[round(y0*320):round(y1*320),round(x0*180):round(x1*180)]
    y=crop@np.array([.2627,.6780,.0593])
    chroma=crop.max(2)-crop.min(2)
    mask=(y>.4)&(y<.86)&(chroma<.10)
    if mask.sum()<30:
        raise ValueError('Not enough neutral pixels. Choose a different neutral ROI; do not grade skin as gray.')
    return np.median(crop[mask],axis=0)


def curve(par):
    xs=np.linspace(0,1,33)
    channels=[]
    for ch in range(3):
        y=forward_hlg(inverse_hlg(xs)*2**(par[ch]+par[3]))
        y+=par[4]*(y-.5)*4*y*(1-y)
        y=np.clip(y,0,1)
        y[0],y[-1]=0,1
        if np.any(np.diff(y)<0):
            raise ValueError('Non-monotonic color curve')
        channels.append(' '.join(f'{x:.5f}/{z:.6f}' for x,z in zip(xs,y)))
    return channels


def grade(source, samples_file, output, choice='software', bitrate='75M'):
    src=Path(source).resolve()
    dest=fresh(output,[src])
    v=video(src)
    if v.get('color_transfer')!='arib-std-b67' or v.get('color_primaries')!='bt2020':
        raise ValueError('This matcher supports HLG/BT.2020 only. SDR/PQ need a separate deliberate workflow.')
    fps_n,fps_d=map(int,v['avg_frame_rate'].split('/'))
    fps=fps_n/fps_d
    if fps != round(fps) or v['width']*16 != v['height']*9:
        raise ValueError('Color sampler currently supports CFR portrait 9:16 masters only')
    fps=int(fps)
    config=json.loads(Path(samples_file).read_text())
    reference=config['reference']
    ref=sample(src,reference['seconds'],reference['roi'])
    ref_lin=inverse_hlg(ref)
    ref_chroma=ref_lin/np.exp(np.mean(np.log(ref_lin)))
    anchors=[]
    parameters={}
    measurements=[]
    for row in config['samples']:
        sec=row['seconds']
        if sec<0 or sec>float(v['duration']):
            raise ValueError('Sample outside video')
        neutral=sample(src,sec,row['roi'])
        lin=inverse_hlg(neutral)
        chroma=lin/np.exp(np.mean(np.log(lin)))
        wb=np.clip(np.log2(ref_chroma/chroma)*.55,-.20,.20)
        wb-=wb.mean()
        ev=float(np.clip(.28*np.log2(inverse_hlg(ref.mean())/inverse_hlg(neutral.mean())),-.28,.14))
        if 'exposure_stops' in row:
            ev=float(row['exposure_stops'])
            if abs(ev)>.28:
                raise ValueError('Explicit exposure override exceeds restrained range')
        par=np.r_[wb,ev,.025]
        anchors.append((sec,par))
        if "scene" in row:
            key=(row["scene"],row.get("broll"))
            if key in parameters: raise ValueError("Duplicate color target")
            parameters[key]=par
        measurements.append(dict(seconds=sec,neutral_hlg=neutral.tolist(),parameters=par.tolist()))
    anchors.append((reference['seconds'],np.zeros(5)))
    anchors.sort(key=lambda a:a[0])
    if len({t for t,_ in anchors})!=len(anchors):
        raise ValueError('Duplicate anchors; omit reference from samples')
    if len(anchors)<2:
        raise ValueError('At least one sample plus reference required')
    def at(t):
        if t<=anchors[0][0]:return anchors[0][1]
        for (ta,pa),(tb,pb) in zip(anchors,anchors[1:]):
            if t<=tb:
                x=(t-ta)/(tb-ta)
                x=x*x*(3-2*x)
                return pa*(1-x)+pb*x
        return anchors[-1][1]
    if 'edit_plan' in config:
        plan_path=Path(samples_file).resolve().parent/config['edit_plan']
        plan=load_plan(plan_path)
        if plan['fps']!=fps or abs(plan['duration']-float(v['duration']))>.04:
            raise ValueError('Color plan must match the master timeline')
        if 'scene' not in reference:
            raise ValueError('Scene-aware reference needs a scene index and optional broll index')
        parameters[(reference['scene'],reference.get('broll'))]=np.zeros(5)
        required={(i,None) for i,_ in enumerate(plan['scenes'])} | {(i,j) for i,s in enumerate(plan['scenes']) for j,_ in enumerate(s['broll'])}
        if set(parameters)!=required:
            raise ValueError('Provide exactly one color sample for each scene and B-roll, except the reference target')
        def ease(x):
            x=np.clip(x,0,1)
            return x*x*(3-2*x)
        def at(t):
            value=parameters[(0,None)].copy()
            for i,tr in enumerate(plan['transitions']):
                start,end=tr['start_frame']/fps,tr['end_frame']/fps
                weight=ease((t-start)/(end-start))
                value=value*(1-weight)+parameters[(i+1,None)]*weight
            for i,scene in enumerate(plan['scenes']):
                for j,broll in enumerate(scene['broll']):
                    start=scene['timeline_frame']/fps+broll['at']
                    end=start+broll['duration']
                    fade=broll['fade']
                    weight=min(ease((t-start)/fade),ease((end-t)/fade)) if fade else float(start<=t<end)
                    if weight:value=value*(1-weight)+parameters[(i,j)]*weight
            return value
        if np.max(np.abs(at(reference['seconds'])))>1e-8:
            raise ValueError('Reference must be inside its stable shot, away from fades/transitions')
    commands=fresh(dest.with_suffix('.commands.txt'))
    lines=[]
    previous=None
    for frame in range(int(v['nb_frames'])):
        t=frame/fps
        par=at(t)
        if previous is not None and np.max(np.abs(par-previous))<.00012:continue
        lines.append(f'{t:.6f} '+', '.join(f"[enter] curves@grade {channel} '{cc}'" for channel,cc in zip(('red','green','blue'),curve(par)))+';')
        previous=par
    commands.write_text('\n'.join(lines)+'\n')
    # Relative safe command path: avoid FFmpeg filter escaping of arbitrary filesystem paths.
    import tempfile
    with tempfile.TemporaryDirectory(prefix='video-grade-') as tmp:
        local=Path(tmp)/'commands.txt'
        local.write_text(commands.read_text())
        filt=f'format=gbrp16le,sendcmd=f={local},curves@grade=interp=pchip,setparams=range=full:color_primaries=bt2020:color_trc=arib-std-b67:colorspace=gbr,scale=out_color_matrix=bt2020:out_range=tv:in_primaries=bt2020:out_primaries=bt2020:in_transfer=arib-std-b67:out_transfer=arib-std-b67,format=yuv420p10le'
        ff(['-i',str(src),'-filter_threads','2','-vf',filt,'-map','0:v:0','-map','0:a:0',*encoder('hlg',choice,bitrate,fps),'-c:a','copy','-movflags','+faststart','-map_metadata','-1',str(dest)],dest.with_suffix('.log'))
    write_json(dest.with_suffix('.grade.json'),dict(reference=reference,reference_neutral=ref.tolist(),measurements=measurements,anchors=[dict(seconds=t,parameters=p.tolist()) for t,p in anchors]))
    verify_audio_copy(src,dest)
    write_json(dest.with_suffix('.validation.json'),verify(dest,v['width'],v['height'],fps,'hlg',float(v['duration'])))
    print(dest)
