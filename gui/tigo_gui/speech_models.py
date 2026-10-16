"""Pinned local neural voices. Download assets only; never upload reply text."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import tarfile
import urllib.request
from .compat import existing_path, LEGACY


VOICES = {
    'ru_RU-dmitri-medium': {
        'name': 'Dmitri Neural', 'locale': 'ru_RU', 'gender': 'Male',
        'sha256': 'c86d0803737de13d441923ff3b3f309482fab8d7af3ec85949942809eb9a3660',
        'size': 67188551,
    },
    'ru_RU-denis-medium': {
        'name': 'Denis Neural', 'locale': 'ru_RU', 'gender': 'Male',
        'sha256': 'efa4c18e0b5e32b81d1b6df36b9d312831e5d545200e27848ef926a4cd930300',
        'size': 67190991,
    },
    'en_US-joe-medium': {
        'name': 'Joe Neural', 'locale': 'en_US', 'gender': 'Male',
        'sha256': '261b903a1fb2ce621e2b5b14233cd41223c3b9f9590f896c11daee4df22d9bd3',
        'size': 67169394,
    },
    'ru_RU-irina-medium': {
        'name': 'Irina Neural', 'locale': 'ru_RU', 'gender': 'Female',
        'sha256': '1fc0f54e5e084fe287c07909f2f6e0ba6d857864cf800e3ab80286a4e8233008',
        'size': 67153308,
    },
    'en_US-lessac-high': {
        'name': 'Lessac High', 'locale': 'en_US', 'gender': 'Female',
        'sha256': '8619d204c7005866fe4f420181dfa79622af6a6222389f0b0818d2af31e0db0e',
        'size': 115545841,
    },
}
DEFAULTS = ('ru_RU-dmitri-medium', 'en_US-joe-medium')
BASE_URL = 'https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/'


def cache_root():
    if os.name == 'nt':
        base = Path(os.environ.get('LOCALAPPDATA', Path.home()/'AppData/Local'))
    else:
        base = Path(os.environ.get('XDG_CACHE_HOME', Path.home()/'.cache'))
    return existing_path(base/'tigo'/'voices', base/LEGACY/'voices')


def installed(path, spec):
    try:
        return (json.loads((path/'verified.json').read_text()) == {'sha256': spec['sha256']}
                and (path/'tokens.txt').is_file() and (path/'espeak-ng-data').is_dir()
                and any(path.glob('*.onnx')))
    except (OSError, ValueError):
        return False


def unpack(archive, staging, prefix):
    """Accept only bounded regular files under the expected archive root."""
    source_args = {'fileobj': archive} if hasattr(archive, 'read') else {'name': archive}
    with tarfile.open(mode='r:bz2', **source_args) as source:
        members = source.getmembers()
        if len(members) > 5000 or sum(m.size for m in members) > 200_000_000:
            raise ValueError('The voice archive exceeds its extraction limit.')
        for member in members:
            parts = PurePosixPath(member.name).parts
            if (not parts or parts[0] != prefix or any(p in ('.', '..') for p in parts)
                    or '\\' in member.name or ':' in member.name
                    or not (member.isdir() or member.isfile())):
                raise ValueError('The voice archive contains an unsafe path or link.')
            target = staging.joinpath(*parts[1:])
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with source.extractfile(member) as src, target.open('wb') as dst:
                    shutil.copyfileobj(src, dst)


def ensure_voice(key, *, root=None, progress=lambda message: None):
    """Serialize writers; interrupted downloads are replaced on the next attempt."""
    from filelock import FileLock
    if key not in VOICES:
        raise ValueError('Unknown neural voice.')
    root = Path(root) if root is not None else cache_root()
    root.mkdir(parents=True, exist_ok=True)
    spec = VOICES[key]
    target = root/key
    progress('Preparing ' + spec['name'] + '.')
    with FileLock(str(root/(key+'.lock')), timeout=90):
        if installed(target, spec):
            return target
        archive, staging = root/(key+'.part'), root/(key+'.staging')
        try:
            progress(f'Downloading {spec["name"]} (about {spec["size"]//1_000_000} MB; first use only).')
            digest, size, last = hashlib.sha256(), 0, 0
            request = urllib.request.Request(BASE_URL+'vits-piper-'+key+'.tar.bz2', headers={'User-Agent': 'Tigo-Desktop/0.9'})
            with urllib.request.urlopen(request, timeout=30) as response, archive.open('wb') as out:
                while block := response.read(256*1024):
                    size += len(block)
                    if size > spec['size']:
                        raise ValueError('The voice download exceeds its pinned size.')
                    out.write(block)
                    digest.update(block)
                    if size-last >= 2_000_000:
                        progress(f'Downloading {spec["name"]}: {size*100//spec["size"]}%')
                        last = size
            if size != spec['size'] or digest.hexdigest() != spec['sha256']:
                raise ValueError('Voice checksum mismatch. No model was installed; retry the download.')
            progress('Verifying and unpacking ' + spec['name'] + '.')
            shutil.rmtree(staging, ignore_errors=True)
            staging.mkdir()
            unpack(archive, staging, 'vits-piper-'+key)
            (staging/'verified.json').write_text(json.dumps({'sha256': spec['sha256']}))
            if not installed(staging, spec):
                raise ValueError('The voice archive is missing required model files.')
            if target.exists():
                shutil.rmtree(target)
            staging.rename(target)
        finally:
            archive.unlink(missing_ok=True)
            shutil.rmtree(staging, ignore_errors=True)
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('voices', nargs='*', metavar='VOICE', help='Voice IDs; omit to install default Russian and English voices')
    args = parser.parse_args()
    if any(key not in VOICES for key in args.voices):
        parser.error('Unknown voice. Available: ' + ', '.join(VOICES))
    for key in args.voices or DEFAULTS:
        print(ensure_voice(key, progress=lambda s: print(s, flush=True)), flush=True)


if __name__ == '__main__':
    main()
