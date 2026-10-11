import argparse
import json
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
from .common import binary, ff, fresh, probe, write_json


def doctor():
    import numpy
    import PIL
    report={'python':sys.version,'platform':platform.platform(),'numpy':numpy.__version__,'Pillow':PIL.__version__}
    for name in ('ffmpeg','ffprobe'):
        path=binary(name)
        report[name]=dict(path=path,version=subprocess.check_output([path,'-version'],stderr=subprocess.STDOUT).decode().splitlines()[0])
    version_match=re.search(r'ffmpeg version (\d+)',report['ffmpeg']['version'])
    if not version_match or int(version_match[1])<9:
        raise ValueError('FFmpeg 9+ required; unversioned development builds need manual verification')
    filters=subprocess.check_output([binary('ffmpeg'),'-hide_banner','-filters'],stderr=subprocess.STDOUT).decode()
    encoders=subprocess.check_output([binary('ffmpeg'),'-hide_banner','-encoders'],stderr=subprocess.STDOUT).decode()
    required=['scale','fps','trim','overlay','xfade','tpad','zoompan','rotate','afftdn','loudnorm','acrossfade','apad','sendcmd','curves']
    missing=[f for f in required if not any(len(line.split())>1 and line.split()[1]==f for line in filters.splitlines())]
    report['missing_filters']=missing
    report['encoders']={e:e in encoders for e in ('libx264','libx265','h264_videotoolbox','hevc_videotoolbox')}
    report['whisper_cli']=shutil.which('whisper-cli')
    help_scale=subprocess.check_output([binary('ffmpeg'),'-hide_banner','-h','filter=scale'],stderr=subprocess.STDOUT).decode()
    report['scale_color_conversion']=all(s in help_scale for s in ('in_transfer','out_transfer','in_primaries','out_primaries'))
    print(json.dumps(report,indent=2))
    if missing or not report['scale_color_conversion']:
        raise ValueError('Required FFmpeg features missing; use the documented FFmpeg 9+ baseline')


def main():
    parser=argparse.ArgumentParser(description='Reproducible local video editing; original files are read-only')
    sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('doctor')
    inventory=sub.add_parser('inventory')
    inventory.add_argument('directory')
    inventory.add_argument('--output',required=True)
    transcription=sub.add_parser('transcribe')
    transcription.add_argument('source')
    transcription.add_argument('--model',required=True)
    transcription.add_argument('--output-dir',required=True)
    transcription.add_argument('--language',default='es')
    transcription.add_argument('--dtw-preset',help='Optional whisper.cpp DTW preset matching the model architecture')
    render=sub.add_parser('render')
    render.add_argument('plan')
    render.add_argument('--output-dir',required=True)
    render.add_argument('--preview',action='store_true')
    render.add_argument('--encoder',choices=['software','videotoolbox'],default='software')
    caps=sub.add_parser('captions')
    caps.add_argument('source')
    caps.add_argument('captions_json')
    caps.add_argument('--output',required=True)
    caps.add_argument('--font',required=True)
    caps.add_argument('--encoder',choices=['software','videotoolbox'],default='software')
    caps.add_argument('--bitrate',default='60M')
    grading=sub.add_parser('grade')
    grading.add_argument('source')
    grading.add_argument('samples_json')
    grading.add_argument('--output',required=True)
    grading.add_argument('--encoder',choices=['software','videotoolbox'],default='software')
    grading.add_argument('--bitrate',default='75M')
    validate=sub.add_parser('validate')
    validate.add_argument('source')
    validate.add_argument('--decode',action='store_true',help='Decode full file and fail on media errors')
    args=parser.parse_args()
    try:
        if args.command=='doctor':doctor()
        elif args.command=='inventory':
            files=sorted(p for p in Path(args.directory).rglob('*') if p.suffix.lower() in ('.mov','.mp4','.mkv','.m4v','.wav','.mp3') and p.is_file())
            dest=fresh(args.output,files)
            write_json(dest,{str(p.resolve()):probe(p) for p in files})
            print(f'{len(files)} media files inspected')
        elif args.command=='transcribe':
            source=Path(args.source).resolve(strict=True)
            model=Path(args.model).resolve(strict=True)
            out=fresh(args.output_dir,[source]);out.mkdir()
            ff(['-i',str(source),'-vn','-ac','1','-ar','16000','-c:a','pcm_s16le',str(out/'speech.wav')],out/'audio.log')
            from .common import run
            cmd=[binary('whisper-cli'),'-m',str(model),'-f',str(out/'speech.wav'),'-l',args.language,'-ojf','-osrt','-of',str(out/'transcript')]
            if args.dtw_preset:cmd+=['-dtw',args.dtw_preset]
            run(cmd,out/'whisper.log')
            print(out)
        elif args.command=='render':
            from .render import render
            render(args.plan,args.output_dir,args.encoder,args.preview)
        elif args.command=='captions':
            from .captions import burn
            burn(args.source,args.captions_json,args.output,args.font,args.encoder,args.bitrate)
        elif args.command=='grade':
            from .grade import grade
            grade(args.source,args.samples_json,args.output,args.encoder,args.bitrate)
        elif args.command=='validate':
            from .common import verify
            print(json.dumps(verify(args.source),indent=2))
            if args.decode:
                subprocess.run([binary('ffmpeg'),'-v','error','-xerror','-i',args.source,'-f','null','-'],check=True)
    except (ValueError,RuntimeError,StopIteration,KeyError,subprocess.CalledProcessError) as error:
        parser.exit(1,f'Error: {error}\n')


if __name__=='__main__':main()
