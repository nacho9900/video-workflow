import json
import math
from pathlib import Path
from .common import binary, digest, encoder, ff, fresh, profile_filter, verify, write_json
from .plan import check_sources, load_plan, sources


def render(plan_file, destination, choice='software', preview=False):
    p = load_plan(plan_file)
    check_sources(p)
    out = fresh(destination, sources(p))
    out.mkdir()
    work = out / 'work'
    work.mkdir()
    logs = out / 'logs'
    logs.mkdir()
    fps = p['fps']
    w, h = (720, round(720*p['height']/p['width']/2)*2) if preview else (p['width'], p['height'])
    rate = p.get('preview_bitrate', '8M') if preview else p.get('bitrate', '75M')
    enc = encoder(p['profile'], choice, rate, fps)
    hdr = p['profile'] == 'hlg'
    pix = 'yuv420p10le' if hdr else 'yuv420p'
    alpha = 'yuva420p10le' if hdr else 'yuva420p'
    overlay = 'yuv420p10' if hdr else 'yuv420'
    hashes = {s: digest(s) for s in sources(p)}
    write_json(out/'source-sha256.json', hashes)
    p.update(render_width=w, render_height=h, encoder=choice, preview=preview)
    write_json(out/'edit-plan.json', p)
    def norm():
        # Center-fill preserves aspect ratio; inspect crop before final approval.
        return f'fps={fps},scale={w}:{h}:force_original_aspect_ratio=increase:flags=lanczos,crop={w}:{h},setsar=1,format={pix},settb=1/{fps},setpts=PTS-STARTPTS'
    for i, s in enumerate(p['scenes']):
        print(f'Scene {i+1}/{len(p["scenes"])}', flush=True)
        args = ['-ss', str(s['in']), '-t', str(s['duration']), '-i', s['file']]
        f = [f'[0:v]{norm()}[v0]']
        for j, b in enumerate(s['broll']):
            args += ['-ss', str(b['in']), '-t', str(b['duration']), '-i', b['file']]
            fade = b['fade']
            effects = '' if fade == 0 else f'fade=t=in:st=0:d={fade}:alpha=1,fade=t=out:st={b["duration"]-fade}:d={fade}:alpha=1,'
            f.append(f'[{j+1}:v]{norm()},format={alpha},{effects}setpts=PTS+{round(b["at"]*fps)}[b{j}]')
            f.append(f'[v{j}][b{j}]overlay=eof_action=pass:repeatlast=0:format={overlay}:enable=\'between(t,{b["at"]},{b["at"]+b["duration"]})\'[v{j+1}]')
        # Two-pass loudnorm. No global denoise without listening to the preview.
        af = p.get('audio_filter', 'highpass=f=70,afftdn=nr=6:nf=-35')
        prefix = af + ',' if af else ''
        measurement = logs/f'{i:02}-loudness.log'
        ff(['-ss', str(s['in']), '-t', str(s['duration']), '-i', s['file'], '-map', '0:a:0',
            '-af', prefix+'loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'], measurement)
        text = measurement.read_text()
        m = json.loads(text[text.rfind('{'):text.rfind('}')+1])
        if not all(math.isfinite(float(m[k])) for k in ('input_i','input_tp','input_lra','input_thresh','target_offset')):
            raise ValueError('Silent/invalid narration; review the source audio')
        loud = 'loudnorm=I=-16:TP=-1.5:LRA=11:' + ':'.join(f'{key}={m[value]}' for key,value in [('measured_I','input_i'),('measured_TP','input_tp'),('measured_LRA','input_lra'),('measured_thresh','input_thresh'),('offset','target_offset')]) + ':linear=true'
        channels = p.get('audio_channels', 'mono')
        if channels not in ('mono', 'stereo'):
            raise ValueError('audio_channels must be mono or stereo')
        f.append(f'[0:a]{prefix}{loud},aresample=48000,aformat=sample_fmts=fltp:channel_layouts={channels},apad=whole_dur={s["duration"]},atrim=duration={s["duration"]},afade=t=in:d=0.015,afade=t=out:st={s["duration"]-.035}:d=0.035,asetpts=PTS-STARTPTS[a]')
        args += ['-filter_complex_threads','2','-filter_complex',';'.join(f),'-map',f'[v{len(s["broll"])}]','-map','[a]',*enc,'-c:a','pcm_s24le','-ar','48000','-frames:v',str(s['frames']),'-t',str(s['duration']),'-map_metadata','-1',str(work/f'scene-{i:02}.mov')]
        ff(args, logs/f'{i:02}-scene.log')
    files = []
    for i, s in enumerate(p['scenes']):
        body = work/f'{i:02}-body.mov'
        files.append(body)
        ff(['-ss',str(s['body_start']/fps),'-i',str(work/f'scene-{i:02}.mov'),'-vf',f'fps={fps},settb=1/{fps},setpts=PTS-STARTPTS','-frames:v',str(s['body_end']-s['body_start']),'-an',*enc,str(body)], logs/f'{i:02}-body.log')
        if i == len(p['scenes'])-1:
            break
        tr = p['transitions'][i]
        n = tr['frames']
        extra = (n-p['overlap_frames'])//2
        handle = n-extra
        if min(s['frames'], p['scenes'][i+1]['frames']) < handle:
            raise ValueError('Insufficient transition handles')
        args = ['-ss',str((s['frames']-handle)/fps),'-t',str(handle/fps),'-i',str(work/f'scene-{i:02}.mov'),'-t',str(handle/fps),'-i',str(work/f'scene-{i+1:02}.mov')]
        fmt = 'yuv444p10le' if hdr else 'yuv444p'
        f = [f'[0:v]fps={fps},format={fmt},tpad=stop_mode=clone:stop={extra},trim=end_frame={n},settb=1/{fps},setpts=PTS-STARTPTS[oa]',f'[1:v]fps={fps},format={fmt},tpad=start_mode=clone:start={extra},trim=end_frame={n},settb=1/{fps},setpts=PTS-STARTPTS[ib]']
        aa, bb = 'oa','ib'
        kind = tr['type']
        duration, offset = n/fps, 0
        if kind.startswith('roll'):
            sign = -1 if kind == 'rollleft' else 1
            for label, incoming, outlabel in [('oa',False,'ra'),('ib',True,'rb')]:
                prog = f'min(1,(1-t/{duration})*2)' if incoming else f'min(1,t/{duration}*2)'
                zprog = f'min(1,(1-on/{n-1})*2)' if incoming else f'min(1,on/{n-1}*2)'
                direction = -sign if incoming else sign
                f.append(f'[{label}]rotate=angle=\'{direction}*0.42*pow({prog},2)\':fillcolor=black,zoompan=z=\'1+0.95*pow({zprog},2)\':x=\'iw/2-iw/zoom/2\':y=\'ih/2-ih/zoom/2\':d=1:s={w}x{h}:fps={fps},{profile_filter(p["profile"])},format={fmt},settb=1/{fps},setpts=PTS-STARTPTS[{outlabel}]')
            f += [f'[ra]trim=end_frame={n//2+2},setpts=PTS-STARTPTS[rac]',f'[rb]trim=start_frame={n//2-2},setpts=PTS-STARTPTS[rbc]']
            aa, bb, kind = 'rac','rbc','fade'
            duration, offset = 4/fps, (n//2-2)/fps
        f.append(f'[{aa}][{bb}]xfade=transition={kind}:duration={duration}:offset={offset}[v]')
        dest = work/f'{i:02}-transition.mov'
        files.append(dest)
        ff([*args,'-filter_complex_threads','2','-filter_complex',';'.join(f),'-map','[v]','-frames:v',str(n),'-an',*enc,str(dest)],logs/f'{i:02}-transition.log')
    # Stitch audio independently: visual transitions may be longer than speech overlaps.
    args, f = [], []
    for i, s in enumerate(p['scenes']):
        args += ['-i',str(work/f'scene-{i:02}.mov')]
        f.append(f'[{i}:a]apad=whole_dur={s["duration"]},atrim=duration={s["duration"]},asetpts=PTS-STARTPTS[a{i}]')
    a = 'a0'
    for i in range(1,len(p['scenes'])):
        f.append(f'[{a}][a{i}]acrossfade=d={p["overlap_frames"]/fps}:c1=tri:c2=tri[m{i}]')
        a = f'm{i}'
    audio = work/'audio.m4a'
    ff([*args,'-filter_complex',';'.join(f),'-map',f'[{a}]','-t',str(p['duration']),'-c:a','aac','-b:a','320k','-ar','48000',str(audio)],logs/'audio.log')
    # Paths containing apostrophes require concat demuxer escaping, not shell quoting.
    def quote(path):
        return "'" + str(path.resolve()).replace("'", "'\\''") + "'"
    concat = work/'concat.txt'
    concat.write_text(''.join('file '+quote(x)+'\n' for x in files))
    master = out/'clean.mov'
    ff(['-safe','0','-f','concat','-i',str(concat),'-i',str(audio),'-map','0:v:0','-map','1:a:0','-c','copy','-t',str(p['duration']),'-movflags','+faststart',str(master)],logs/'concat.log')
    report = verify(master,w,h,fps,p['profile'],p['duration'])
    if any(digest(s) != hsh for s,hsh in hashes.items()):
        raise RuntimeError('An input changed during rendering')
    write_json(out/'validation.json',report)
    print(master, flush=True)
    return master
