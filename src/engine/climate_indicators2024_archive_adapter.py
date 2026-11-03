"""Peer-reviewed Indicators of Global Climate Change 2024: frozen Zenodo archive."""
import release_runtime
import argparse
import csv
import hashlib
import io
import json
import requests
import zipfile
URL = 'https://zenodo.org/api/records/15639576/files/ClimateIndicator/data-v2025.06.11.zip/content'
RECORD = 'https://zenodo.org/records/15639576'
ARTICLE = 'https://doi.org/10.5194/essd-17-2641-2025'
MD5 = '620c3673fcfc6dc2113a28e6815423db'
ROOT = 'ClimateIndicator-data-77a147e/'
MAX_ZIP = 2000000
MAX_MEMBER = 4000000

def _archive():
    with requests.get(URL, timeout=30, stream=True) as r:
        r.raise_for_status()
        raw = bytearray()
        for part in r.iter_content(65536):
            raw.extend(part)
            if len(raw) > MAX_ZIP:
                raise ValueError('archive exceeds size limit')
    if hashlib.md5(raw).hexdigest() != MD5:
        raise ValueError('archive does not match Zenodo published checksum')
    return zipfile.ZipFile(io.BytesIO(raw))

def _files(z):
    return sorted((x.filename[len(ROOT):] for x in z.infolist() if x.filename.startswith(ROOT + 'data/') and x.filename.endswith('.csv') and (not x.is_dir()) and (x.file_size <= MAX_MEMBER)))

def catalog(keyword='', limit=100):
    if not isinstance(keyword, str) or len(keyword) > 150 or isinstance(limit, bool) or (not isinstance(limit, int)) or (not 1 <= limit <= 500):
        raise ValueError('invalid keyword or limit')
    with _archive() as z:
        matches = [x for x in _files(z) if keyword.casefold() in x.casefold()]
    return {'source': URL, 'record': RECORD, 'article': ARTICLE, 'edition': 'v2025.06.11', 'archive_published': '2025-06-11', 'article_published': '2025-06-19', 'license': 'CC BY 4.0', 'matched_count': len(matches), 'returned': min(len(matches), limit), 'files': matches[:limit], 'note': 'Peer-reviewed research consortium, not a government statistical release. Individual files have different sources, baselines, methods, uncertainty, and observed versus modeled status.'}

def data(path, keyword='', offset=0, limit=100):
    if not isinstance(path, str) or len(path) > 300 or (not isinstance(keyword, str)) or (len(keyword) > 150):
        raise ValueError('invalid path or keyword')
    if any((isinstance(v, bool) or not isinstance(v, int) for v in (offset, limit))) or offset < 0 or (not 1 <= limit <= 500):
        raise ValueError('invalid pagination')
    with _archive() as z:
        if path not in _files(z):
            raise ValueError('file not in archive data CSV catalog')
        info = z.getinfo(ROOT + path)
        if info.file_size > MAX_MEMBER:
            raise ValueError('member exceeds size limit')
        reader = csv.reader(io.StringIO(z.read(info).decode('utf-8-sig'), newline=''))
        header = next(reader)
        rows = []
        count = 0
        for row in reader:
            if keyword.casefold() not in ' '.join(row).casefold():
                continue
            if offset <= count < offset + limit:
                rows.append(row)
            count += 1
        metadata_path = path[:-4] + '.metadata.yml'
        metadata = None
        if ROOT + metadata_path in z.namelist():
            mi = z.getinfo(ROOT + metadata_path)
            if mi.file_size > MAX_MEMBER:
                raise ValueError('metadata exceeds size limit')
            metadata = z.read(mi).decode('utf-8-sig')
    return {'source': URL, 'record': RECORD, 'article': ARTICLE, 'edition': 'v2025.06.11', 'archive_published': '2025-06-11', 'article_published': '2025-06-19', 'license': 'CC BY 4.0', 'path': path, 'header': header, 'metadata_path': metadata_path if metadata is not None else None, 'metadata_text': metadata, 'matched_count': count, 'offset': offset, 'returned': len(rows), 'raw_rows': rows, 'note': 'Raw CSV strings and positional columns retained. Read file metadata for units, baseline, observation/model, time bounds and uncertainty. Missing metadata is not evidence of data quality; do not treat as zero.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('catalog')
    q.add_argument('--keyword', default='')
    q.add_argument('--limit', type=int, default=100)
    q = s.add_parser('data')
    q.add_argument('path')
    q.add_argument('--keyword', default='')
    q.add_argument('--offset', type=int, default=0)
    q.add_argument('--limit', type=int, default=100)
    a = p.parse_args()
    out = catalog(a.keyword, a.limit) if a.cmd == 'catalog' else data(a.path, a.keyword, a.offset, a.limit)
    print(json.dumps(out, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
