import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess


def binary(name):
    value = os.environ.get(name.upper().replace('-', '_'), name)
    found = shutil.which(value)
    if not found:
        raise ValueError(f'Missing {name}; install it or set {name.upper().replace("-", "_")}')
    return found


def run(args, log=None):
    if log:
        Path(log).parent.mkdir(parents=True, exist_ok=True)
        with Path(log).open('w') as f:
            result = subprocess.run(args, stdout=f, stderr=f)
        if result.returncode:
            raise RuntimeError(f'Command failed; see {log}\n{Path(log).read_text()[-4000:]}')
    else:
        subprocess.run(args, check=True)


def ff(args, log=None):
    run([binary('ffmpeg'), '-hide_banner', '-nostdin', '-y', *args], log)


def probe(path):
    return json.loads(subprocess.check_output([binary('ffprobe'), '-v', 'error',
        '-show_streams', '-show_format', '-of', 'json', str(path)]))


def video(path):
    return next(s for s in probe(path)['streams'] if s['codec_type'] == 'video')


def write_json(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def fresh(path, sources=()):
    p = Path(path).resolve()
    if p.exists():
        raise ValueError(f'Refusing to overwrite existing output: {p}')
    if p in {Path(s).resolve() for s in sources}:
        raise ValueError('Output is an input')
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def encoder(profile, choice, bitrate, fps):
    if profile not in ('hlg', 'sdr') or choice not in ('software', 'videotoolbox'):
        raise ValueError('Unsupported profile/encoder')
    hdr = profile == 'hlg'
    codec = ('hevc' if hdr else 'h264') + '_videotoolbox' if choice == 'videotoolbox' else ('libx265' if hdr else 'libx264')
    args = ['-c:v', codec, '-pix_fmt', ('p010le' if choice == 'videotoolbox' else 'yuv420p10le') if hdr else 'yuv420p',
            '-b:v', bitrate, '-g', str(fps), '-tag:v', 'hvc1' if hdr else 'avc1']
    if choice == 'software':
        args += ['-preset', 'medium']
    if hdr:
        args += ['-profile:v', 'main10']
    args += ['-color_primaries', 'bt2020' if hdr else 'bt709',
             '-color_trc', 'arib-std-b67' if hdr else 'bt709',
             '-colorspace', 'bt2020nc' if hdr else 'bt709', '-color_range', 'tv']
    return args


def profile_filter(profile):
    hdr = profile == 'hlg'
    return ('setparams=range=limited:color_primaries=' + ('bt2020' if hdr else 'bt709')
            + ':color_trc=' + ('arib-std-b67' if hdr else 'bt709')
            + ':colorspace=' + ('bt2020nc' if hdr else 'bt709'))


def verify(path, width=None, height=None, fps=None, profile=None, duration=None):
    p = probe(path)
    v = next(s for s in p['streams'] if s['codec_type'] == 'video')
    a = next((s for s in p['streams'] if s['codec_type'] == 'audio'), None)
    for field, target in [('width', width), ('height', height)]:
        if target is not None and v[field] != target:
            raise ValueError(f'Unexpected {field}: {v[field]}')
    if fps is not None:
        n, d = map(int, v['avg_frame_rate'].split('/'))
        if abs(n / d - fps) > .001:
            raise ValueError('Unexpected frame rate')
    if profile == 'hlg' and (v.get('color_transfer') != 'arib-std-b67' or v.get('color_primaries') != 'bt2020' or v.get('pix_fmt') != 'yuv420p10le'):
        raise ValueError('HDR HLG / BT.2020 / 10-bit was not preserved')
    if profile is not None and (v.get('color_space') != ('bt2020nc' if profile=='hlg' else 'bt709') or v.get('color_range') != 'tv'):
        raise ValueError('Unexpected color matrix or range')
    if profile == 'sdr' and v.get('color_transfer') != 'bt709':
        raise ValueError('SDR transfer mismatch')
    if duration is not None and abs(float(v['duration']) - duration) > .04:
        raise ValueError('Video duration mismatch')
    if abs(float(v.get('start_time',0)))>.001 or (a and abs(float(a.get('start_time',0)))>.001):
        raise ValueError('A/V does not start at zero')
    if duration is not None and fps is not None and int(v.get('nb_frames',-1)) != round(duration*fps):
        raise ValueError('Unexpected frame count')
    if a and abs(float(v['duration']) - float(a['duration'])) > .05:
        raise ValueError('A/V durations differ by more than 50ms')
    return p


def audio_hash(path):
    return subprocess.check_output([binary('ffmpeg'),'-v','error','-i',str(path),'-map','0:a:0','-c:a','copy','-f','hash','-']).decode().strip()


def verify_audio_copy(source, dest):
    if audio_hash(source) != audio_hash(dest):
        raise ValueError('Audio changed in a stage that promises bitstream copy')
