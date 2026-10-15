"""Explicit local file selection and bounded previews for app-server inputs."""
import codecs
from pathlib import Path
import stat
from PySide6.QtCore import QUrl
from PySide6.QtGui import QImageReader

MAX_FILES = 10
MAX_BYTES = 20 * 1024 * 1024
IMAGE_SUFFIXES = {'.png','.jpg','.jpeg','.webp','.gif','.bmp'}


def inspect_file(value):
    url = value if isinstance(value,QUrl) else QUrl.fromLocalFile(str(value)) if Path(str(value)).is_absolute() else QUrl(str(value))
    if url.scheme():
        if not url.isLocalFile() or url.host() not in ('','localhost'):
            raise ValueError('Only local files can be attached.')
        path = Path(url.toLocalFile())
    else:
        path = Path(str(value))
    path = path.resolve(strict=True)
    info = path.stat()
    if not stat.S_ISREG(info.st_mode):
        raise ValueError('Choose a regular file, not a folder or device.')
    if info.st_size > MAX_BYTES:
        raise ValueError('Attachments are limited to 20 MB per file.')
    kind = 'image' if path.suffix.lower() in IMAGE_SUFFIXES else 'file'
    if kind == 'image':
        reader = QImageReader(str(path))
        size = reader.size()
        if not reader.canRead() or size.width() <= 0 or size.height() <= 0 or size.width()*size.height() > 20_000_000:
            raise ValueError('Choose a readable image up to 20 megapixels.')
        preview = f'{size.width()} x {size.height()}'
    else:
        with path.open('rb') as stream:
            chunk = stream.read(8000)
        try:
            preview = codecs.getincrementaldecoder('utf-8')().decode(chunk, final=info.st_size <= len(chunk))
            if '\x00' in preview: raise UnicodeError()
        except UnicodeError:
            preview = 'Binary file reference. Codex can inspect it with available tools.'
    return {'name':path.name,'path':str(path),'url':QUrl.fromLocalFile(str(path)).toString(),
            'kind':kind,'size':info.st_size,'mtime':str(info.st_mtime_ns),'preview':preview}


def validate_files(files):
    if len(files) > MAX_FILES:
        raise ValueError('Attach up to 10 files per request.')
    result = []
    for saved in files:
        current = inspect_file(saved['path'])
        if current['size'] != saved.get('size') or current['mtime'] != saved.get('mtime'):
            raise ValueError(f"Attachment changed: {current['name']}. Remove it and attach it again to review.")
        if saved.get('clipboard'):
            current['clipboard'] = True
        result.append(current)
    return result

