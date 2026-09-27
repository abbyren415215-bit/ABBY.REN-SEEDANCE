#!/usr/bin/env python3
"""Assemble four reviewed 30-second clips. No network or generation side effects."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def inspect(exe, path):
    p = subprocess.run([exe, '-hide_banner', '-i', str(path)], capture_output=True, text=True)
    duration = re.search(r'Duration: (\d+):(\d+):(\d+(?:\.\d+)?)', p.stderr)
    if not duration or not re.search(r'Stream .*Video:', p.stderr):
        raise ValueError(f'无法识别视频：{path.name}')
    h, m, s = map(float, duration.groups())
    return {'duration': h * 3600 + m * 60 + s,
            'has_audio': bool(re.search(r'Stream .*Audio:', p.stderr))}


def assemble(manifest, output, exe):
    data = json.loads(manifest.read_text())
    clips = data.get('clips', [])
    if len(clips) != 4 or [c.get('scene') for c in clips] != [1, 2, 3, 4]:
        raise ValueError('必须按1、2、3、4场顺序提供四个版本。')
    width, height = data.get('width'), data.get('height')
    if not all(type(v) is int and v > 0 and v % 2 == 0 for v in (width, height)):
        raise ValueError('需要已确认的偶数画布宽高。')
    if output.exists() or output.with_suffix('.json').exists():
        raise ValueError('输出已存在，请使用新版本名，保留旧文件。')
    sources = []
    for c in clips:
        if c.get('qa_status') != 'passed':
            raise ValueError(f'第{c["scene"]}场尚未完成审片。')
        path = Path(c.get('path', ''))
        path = (manifest.parent / path).resolve() if not path.is_absolute() else path
        if not path.is_file() or digest(path) != c.get('sha256'):
            raise ValueError(f'第{c["scene"]}场文件缺失或已变更，需要重新核对版本。')
        meta = inspect(exe, path)
        if abs(meta['duration'] - 30) > 0.25:
            raise ValueError(f'第{c["scene"]}场为{meta["duration"]}秒，不能自动变速或补片凑30秒。')
        sources.append((path, meta))
    expected = sum(meta['duration'] for _, meta in sources)
    if abs(expected - 120) > 0.5:
        raise ValueError('合计时长偏离120秒，先核对素材。')
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.assembling-', suffix='.mp4', dir=output.parent)
    os.close(fd)
    temp = Path(temporary)
    cmd = [exe, '-hide_banner', '-loglevel', 'error', '-y']
    for path, _ in sources:
        cmd += ['-i', str(path)]
    filters = []
    for i, (_, meta) in enumerate(sources):
        filters.append(f'[{i}:v:0]setpts=PTS-STARTPTS,scale={width}:{height}:force_original_aspect_ratio=decrease:force_divisible_by=2,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30,format=yuv420p[v{i}]')
        d = meta['duration']
        if meta['has_audio']:
            filters.append(f'[{i}:a:0]asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,apad,atrim=duration={d}[a{i}]')
        else:
            filters.append(f'anullsrc=r=48000:cl=stereo,atrim=duration={d},asetpts=PTS-STARTPTS[a{i}]')
    inputs = ''.join(f'[v{i}][a{i}]' for i in range(4))
    filters.append(inputs + 'concat=n=4:v=1:a=1[v][a]')
    cmd += ['-filter_complex', ';'.join(filters), '-map', '[v]', '-map', '[a]',
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '18', '-c:a', 'aac',
            '-b:a', '192k', '-map_metadata', '-1', '-movflags', '+faststart', str(temp)]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        meta = inspect(exe, temp)
        if abs(meta['duration'] - expected) > 0.25:
            raise ValueError('合成后时长异常，未交付输出。')
        # Hard linking fails instead of overwriting if another run created this name.
        os.link(temp, output)
        report = {'status': 'assembled_pending_user_review', 'output': output.name,
                  'duration': meta['duration'], 'sha256': digest(output),
                  'width': width, 'height': height, 'fps': 30,
                  'source_versions': [{k: c[k] for k in ('scene', 'sha256')} for c in clips],
                  'note': '保留原有音轨；未自动检查或移除其中的音乐/字幕，内容审片由助手另行执行。'}
        with output.with_suffix('.json').open('x') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        return report
    finally:
        temp.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--ffmpeg', default=shutil.which('ffmpeg'))
    args = parser.parse_args()
    if not args.ffmpeg:
        parser.error('需要本机FFmpeg路径；不自动下载或提交任何生成。')
    try:
        print(json.dumps(assemble(args.manifest.resolve(), args.output.resolve(), args.ffmpeg), ensure_ascii=False, indent=2))
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f'合成未完成：{exc}\n')


if __name__ == '__main__':
    main()
