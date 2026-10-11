import json
from pathlib import Path
import subprocess
from PIL import Image, ImageDraw, ImageFont
from .common import binary, encoder, fresh, verify, video, write_json, verify_audio_copy


def srt(captions):
    def stamp(t):
        ms = round(t*1000)
        return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
    return '\n\n'.join(f'{i+1}\n{stamp(c["start"])} --> {stamp(c["end"])}\n{c["text"]}' for i,c in enumerate(captions))+'\n'


def burn(source, captions_file, output, font_file, choice='software', bitrate='60M'):
    src = Path(source).resolve()
    dest = fresh(output, [src])
    caps = json.loads(Path(captions_file).read_text())
    font_path = Path(font_file).resolve(strict=True)
    v = video(src)
    w,h = v['width'],v['height']
    n,d = map(int,v['avg_frame_rate'].split('/'))
    fps = n/d
    if fps != round(fps):
        raise ValueError('Caption renderer expects a CFR master with integer FPS')
    fps = int(fps)
    frames = int(v['nb_frames'])
    profile = 'hlg' if v.get('color_transfer') == 'arib-std-b67' else 'sdr'
    if v.get('color_transfer') not in ('arib-std-b67','bt709'):
        raise ValueError('Unknown color transfer')
    strip = round(w*300/2160/2)*2
    size = max(10,round(w*144/2160))
    font = ImageFont.truetype(str(font_path),size)
    prev = 0
    for c in caps:
        if c['start'] < prev or c['end'] <= c['start'] or c['end'] > frames/fps+.001:
            raise ValueError('Captions overlap or exceed video duration')
        if ImageDraw.Draw(Image.new('RGBA',(w,strip))).textbbox((0,0),c['text'],font=font)[2] + w*96/2160 > w*.94:
            raise ValueError(f'Caption too long: {c["text"]!r}. Split phrase; do not shrink the font.')
        prev = c['end']
    alpha = 'yuva420p10le' if profile == 'hlg' else 'yuva420p'
    conversion = 'scale=in_primaries=bt709:in_transfer=iec61966-2-1:out_primaries=bt2020:out_transfer=arib-std-b67:out_color_matrix=bt2020' if profile == 'hlg' else 'scale=in_primaries=bt709:in_transfer=iec61966-2-1:out_primaries=bt709:out_transfer=bt709:out_color_matrix=bt709'
    f = f'[1:v]{conversion},format={alpha}[c];[0:v][c]overlay=0:{round(h*.7526)}:format={"yuv420p10" if profile=="hlg" else "yuv420"}:shortest=1[v]'
    log = dest.with_suffix('.log')
    cmd = [binary('ffmpeg'),'-y','-hide_banner','-nostdin','-i',str(src),'-f','rawvideo','-pixel_format','rgba','-video_size',f'{w}x{strip}','-framerate',str(fps),'-i','pipe:0','-filter_complex_threads','2','-filter_complex',f,'-map','[v]','-map','0:a:0',*encoder(profile,choice,bitrate,fps),'-c:a','copy','-frames:v',str(frames),'-movflags','+faststart','-map_metadata','-1',str(dest)]
    blank = Image.new('RGBA',(w,strip)).tobytes()
    index = 0
    cache = {}
    with log.open('w') as logfile:
        proc = subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=logfile,stderr=logfile)
        try:
            for frame in range(frames):
                t = frame/fps
                while index < len(caps) and t >= caps[index]['end']:
                    index += 1
                    cache.clear()
                data = blank
                if index < len(caps) and t >= caps[index]['start']:
                    c = caps[index]
                    elapsed = t-c['start']
                    phase = 0 if elapsed < 2/fps else 1 if elapsed < 4/fps else 2
                    if phase not in cache:
                        image = Image.new('RGBA',(w,strip))
                        draw = ImageDraw.Draw(image)
                        box = draw.textbbox((0,0),c['text'],font=font)
                        tw,th = box[2]-box[0],box[3]-box[1]
                        x,y = (w-tw)/2,(strip-th)/2-box[1]
                        pad = w*48/2160
                        draw.rounded_rectangle((x-pad,(strip-th)/2-pad*.46,x+tw+pad,(strip+th)/2+pad*.46),radius=max(1,w*4/2160),fill=(0,0,0,255))
                        draw.text((x,y),c['text'],font=font,fill=(255,255,0,255))
                        scale, opacity = [(0.94,.35),(.98,.75),(1,1)][phase]
                        if phase != 2:
                            small = image.resize((round(w*scale),round(strip*scale)),Image.Resampling.LANCZOS)
                            image = Image.new('RGBA',(w,strip))
                            image.paste(small,((w-small.width)//2,(strip-small.height)//2))
                            image.putalpha(image.getchannel('A').point(lambda a: round(a*opacity)))
                        cache[phase] = image.tobytes()
                    data = cache[phase]
                proc.stdin.write(data)
            proc.stdin.close()
            if proc.wait():
                raise RuntimeError(f'Caption render failed: {log.read_text()[-3000:]}')
        except BaseException:
            proc.kill()
            proc.wait()
            raise
    verify_audio_copy(src,dest)
    write_json(dest.with_suffix('.validation.json'),verify(dest,w,h,fps,profile,frames/fps))
    fresh(dest.with_suffix('.srt')).write_text(srt(caps))
    print(dest)
