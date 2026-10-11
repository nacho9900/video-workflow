import copy
import json
import math
from pathlib import Path
from .common import probe

TRANSITIONS = {'fadeblack', 'fade', 'smoothleft', 'smoothright', 'zoomin', 'rollleft', 'rollright'}


def compile_plan(raw, root):
    p = copy.deepcopy(raw)
    fps = p['fps']
    if not isinstance(fps, int) or fps <= 0:
        raise ValueError('fps must be a positive integer')
    if p['profile'] not in ('hlg', 'sdr'):
        raise ValueError('Explicit hlg or sdr profile required')
    if any(not isinstance(p[k], int) or p[k] <= 0 or p[k] % 2 for k in ('width', 'height')):
        raise ValueError('width/height must be positive even integers')
    overlap = round(p.get('audio_overlap', .2) * fps)
    if overlap < 1:
        raise ValueError('audio_overlap must be at least one frame')
    p['overlap_frames'] = overlap
    clock = 0
    if not p['scenes']:
        raise ValueError('At least one scene required')
    for s in p['scenes']:
        s['file'] = str((root / s['file']).resolve())
        start = round(s['in'] * fps)
        end = round(s['out'] * fps)
        if start < 0 or end - start <= overlap:
            raise ValueError('Invalid scene trim')
        s.update(in_frame=start, frames=end-start, timeline_frame=clock,
                 duration=(end-start)/fps)
        s['in'] = start / fps
        s['out'] = end / fps
        clock += s['frames'] - overlap
        for b in s.setdefault('broll', []):
            b['file'] = str((root / b['file']).resolve())
            for k in ('in', 'at', 'duration'):
                b[k] = round(b[k] * fps) / fps
            fade = b.setdefault('fade', .16)
            if b['in'] < 0 or b['at'] < 0 or b['duration'] <= 0 or b['at'] + b['duration'] > s['duration'] + 1e-6 or fade < 0 or fade * 2 > b['duration']:
                raise ValueError('B-roll is outside scene or has invalid fades')
    p['frames'] = clock + overlap
    p['duration'] = p['frames'] / fps
    transitions = p.get('transitions', [])
    if len(transitions) != len(p['scenes']) - 1:
        raise ValueError('Exactly one transition per scene boundary required')
    for i, t in enumerate(transitions):
        frames = round(t['duration'] * fps)
        if t['type'] not in TRANSITIONS or frames < max(4, overlap) or (frames-overlap) % 2:
            raise ValueError('Transition needs supported type and frame count with same parity as audio overlap')
        start = p['scenes'][i+1]['timeline_frame'] - (frames-overlap)//2
        t.update(frames=frames, duration=frames/fps, start_frame=start, end_frame=start+frames)
    for i, s in enumerate(p['scenes']):
        left = 0 if i == 0 else transitions[i-1]['end_frame'] - s['timeline_frame']
        right = s['frames'] if i == len(p['scenes'])-1 else transitions[i]['start_frame'] - s['timeline_frame']
        if left < 0 or right > s['frames'] or right <= left:
            raise ValueError('Scene too short for selected transitions')
        s['body_start'] = left
        s['body_end'] = right
    prev = 0
    for c in p.setdefault('captions', []):
        if not isinstance(c['text'], str) or not c['text'].strip() or not math.isfinite(c['start']) or not math.isfinite(c['end']):
            raise ValueError('Invalid caption')
        c['start'] = round(c['start'] * fps) / fps
        c['end'] = round(c['end'] * fps) / fps
        if c['start'] < prev or c['end'] <= c['start'] or c['end'] > p['duration']:
            raise ValueError('Captions must be ordered, non-overlapping, and within timeline')
        prev = c['end']
    return p


def load_plan(path):
    path = Path(path).resolve()
    return compile_plan(json.loads(path.read_text()), path.parent)


def sources(p):
    return sorted({s['file'] for s in p['scenes']} | {b['file'] for s in p['scenes'] for b in s['broll']})


def check_sources(p):
    info = {}
    for file in sources(p):
        q = probe(file)
        v = next(s for s in q['streams'] if s['codec_type'] == 'video')
        expected = 'arib-std-b67' if p['profile'] == 'hlg' else 'bt709'
        primaries = 'bt2020' if p['profile'] == 'hlg' else 'bt709'
        if v.get('color_transfer') != expected or v.get('color_primaries') != primaries:
            raise ValueError(f'{file}: mixed/unknown color profile. Convert deliberately first; never just retag it.')
        info[file] = q
    for s in p['scenes']:
        if not any(q['codec_type'] == 'audio' for q in info[s['file']]['streams']):
            raise ValueError('Narration scene needs an audio track')
        for b in [dict(file=s['file'], **{'in': s['in'], 'duration': s['duration']}), *s['broll']]:
            dur = float(info[b['file']]['format']['duration'])
            if b['in'] + b['duration'] > dur + 1/p['fps']:
                raise ValueError(f'Trim exceeds source: {b["file"]}')
    return info
