"""Search locally downloaded ACS 2026 eBook MARC; noncommercial CC BY-NC-ND 4.0."""
import release_runtime
import re
import zipfile
from pathlib import Path
DEFAULT = release_runtime.home() / 'Library/Application Support/ResearchDatabaseToolkit/acs/2026_eBooks.zip'
SOURCE = 'https://connect.acspubs.org/marc'
LICENSE = 'https://creativecommons.org/licenses/by-nc-nd/4.0/'

def _fields(data):
    if len(data) < 25 or not data[:5].isdigit() or int(data[:5]) != len(data):
        raise ValueError('unexpected MARC length')
    base = int(data[12:17])
    directory = data[24:base - 1]
    if len(directory) % 12 or data[base - 1] != 30:
        raise ValueError('unexpected MARC directory')
    result = {}
    for i in range(0, len(directory), 12):
        e = directory[i:i + 12]
        tag = e[:3].decode('ascii')
        size = int(e[3:7])
        start = int(e[7:12])
        raw = data[base + start:base + start + size - 1]
        if tag not in {'020', '024', '245', '856'}:
            continue
        sub = []
        for chunk in raw[2:].split(b'\x1f')[1:]:
            if chunk:
                sub.append((chr(chunk[0]), chunk[1:].decode('utf-8').strip()))
        result.setdefault(tag, []).append(sub)
    return result

def search(keyword, limit=10, path=DEFAULT, *, offset=0):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100:
        raise ValueError('keyword must contain 1–100 characters')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 20):
        raise ValueError('limit must be 1–20')
    if type(offset) is not int or offset < 0:
        raise ValueError('offset must be a nonnegative integer')
    rows = []
    with zipfile.ZipFile(path) as archive:
        files = [x for x in archive.infolist() if x.filename.endswith('.mrc') and (not x.is_dir())]
        if len(files) > 1000 or any((x.file_size > 100000 for x in files)):
            raise ValueError('unexpected archive size')
        for f in files:
            fields = _fields(archive.read(f))
            values = lambda tag, code: [v for field in fields.get(tag, []) for c, v in field if c == code]
            title = ' '.join(values('245', 'a') + values('245', 'b') + values('245', 'n') + values('245', 'p'))
            if keyword.strip().casefold() not in title.casefold():
                continue
            doi = [v for field in fields.get('024', []) if ('2', 'doi') in field for c, v in field if c == 'a']
            rows.append({'title': title, 'responsibility': values('245', 'c'), 'doi': doi[0] if doi else None, 'isbn': values('020', 'a'), 'url': next(iter(values('856', 'u')), None)})
    return {'source': 'Local MARC archive (provenance and version unverified)', 'source_url': None, 'license': None, 'reference_source_url': SOURCE, 'reference_license_url': LICENSE, 'file': str(path), 'file_records': len(files), 'keyword': keyword.strip(), 'matches': len(rows), 'offset': offset, 'returned': len(rows[offset:offset + limit]), 'next_offset': offset + limit if offset + limit < len(rows) else None, 'truncated': offset + limit < len(rows), 'items': rows[offset:offset + limit], 'note': '本地书目文件的来源、版本和许可未经核验；参考网址仅描述预期资料，不代表学校订购或全文权限。每次重新读取本地文件；替换文件后结果顺序可能变化。'}
