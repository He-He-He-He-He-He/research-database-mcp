"""UN WPP 2022 medium-variant demographics, selectively read from official archive."""
import release_runtime
import argparse, csv, hashlib, io, json, os, re, tempfile, zipfile
from pathlib import Path
import requests
URL = 'https://population.un.org/wpp/assets/Excel%20Files/5_Archive/WPP2022-CSV-data.zip'
CATALOG = 'https://population.un.org/wpp/assets/downloads.json'
MEMBER = 'CSV_FILES/WPP2022_Demographic_Indicators_Medium.csv'
SHA = '3e57e009e4bc6bcd00e7c51f6ba84dba36337a611f7138b7993550c7345088e5'
SIZE = 3522206105
BLOCK = 1048576
CACHE = release_runtime.home() / '.cache' / 'zju-research-toolkit' / 'WPP2022_Demographic_Indicators_Medium.csv'
UNITS = {'TPopulation1July': 'thousands of people', 'TFR': 'births per woman', 'LEx': 'years'}

class RangeFile(io.RawIOBase):

    def __init__(self):
        self.pos = 0
        self.blocks = {}
        self.session = requests.Session()
        self.version = None
        self.last_modified = None

    def seekable(self):
        return True

    def readable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, offset, whence=0):
        p = offset if whence == 0 else self.pos + offset if whence == 1 else SIZE + offset
        if p < 0:
            raise ValueError('negative seek')
        self.pos = p
        return p

    def read(self, n=-1):
        if self.pos >= SIZE:
            return b''
        n = min(SIZE - self.pos, n if n >= 0 else SIZE - self.pos)
        if n > 25000000:
            raise ValueError('range request exceeds limit')
        out = bytearray()
        while n:
            idx = self.pos // BLOCK
            a = idx * BLOCK
            b = min(SIZE - 1, a + BLOCK - 1)
            if idx not in self.blocks:
                if len(self.blocks) >= 24:
                    raise ValueError('range download budget exceeded')
                r = self.session.get(URL, headers={'Range': f'bytes={a}-{b}'}, timeout=40)
                r.raise_for_status()
                if r.status_code != 206 or r.headers.get('Content-Range') != f'bytes {a}-{b}/{SIZE}' or len(r.content) != b - a + 1:
                    raise ValueError('invalid range response or archive changed')
                stamp = (r.headers.get('ETag'), r.headers.get('Last-Modified'))
                if self.version is None:
                    self.version = stamp
                    self.last_modified = stamp[1]
                elif stamp != self.version:
                    raise ValueError('archive changed during retrieval')
                self.blocks[idx] = r.content
            chunk = self.blocks[idx]
            offset = self.pos - a
            k = min(n, len(chunk) - offset)
            out.extend(chunk[offset:offset + k])
            self.pos += k
            n -= k
        return bytes(out)

    def close(self):
        self.session.close()
        super().close()

def _fetch():
    if CACHE.is_file():
        with CACHE.open('rb') as f:
            head = f.readline(1024)
        if head.startswith(b'SortOrder,LocID,') and CACHE.stat().st_size == 20497739 and (hashlib.sha256(CACHE.read_bytes()).hexdigest() == SHA):
            return (CACHE, None, None)
        raise ValueError('existing cache does not match expected shape; review manually')
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    tmp = None
    try:
        with RangeFile() as f, zipfile.ZipFile(f) as z:
            info = z.getinfo(MEMBER)
            if info.file_size != 20497739 or info.compress_size != 8148344:
                raise ValueError('archive member changed; review manually')
            with tempfile.NamedTemporaryFile(dir=CACHE.parent, prefix='.wpp2022-', delete=False) as dest:
                tmp = Path(dest.name)
                with z.open(info) as source:
                    while True:
                        chunk = source.read(262144)
                        if not chunk:
                            break
                        dest.write(chunk)
            stamp = f.last_modified
            membertime = info.date_time
        if hashlib.sha256(tmp.read_bytes()).hexdigest() != SHA:
            raise ValueError('member checksum changed; review manually')
        os.replace(tmp, CACHE)
        return (CACHE, stamp, membertime)
    finally:
        if tmp and tmp.exists():
            tmp.unlink()

def query(iso3, start, end):
    if not isinstance(iso3, str) or not re.fullmatch('[A-Z]{3}', iso3) or any((type(v) is not int for v in (start, end))) or (not 1950 <= start <= end <= 2100):
        raise ValueError('invalid ISO3 or years')
    path, modified, membertime = _fetch()
    h = hashlib.sha256()
    result = []
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''):
            h.update(b)
    with path.open(encoding='utf-8-sig', newline='') as f:
        rows = csv.DictReader(f)
        required = {'ISO3_code', 'Location', 'Time', 'Variant', *UNITS}
        if not required.issubset(rows.fieldnames or []):
            raise ValueError('unexpected source columns')
        for row in rows:
            if row['ISO3_code'] == iso3 and row['Time'].isdigit() and (start <= int(row['Time']) <= end):
                result.append({k: row[k] for k in ('ISO3_code', 'Location', 'Time', 'Variant', *UNITS)})
    return {'source_archive': URL, 'official_catalog': CATALOG, 'member': MEMBER, 'member_sha256': h.hexdigest(), 'archive_last_modified_on_download': modified, 'member_timestamp_on_download': list(membertime) if membertime else None, 'edition': '2022 revision, medium variant', 'units': UNITS, 'records': result, 'note': 'UN population estimates and projections, not a census count; 2022 onwards are projections in this revision. Zip member timestamp observed 2022-08-02 and archive HTTP Last-Modified observed 2024-12-13; timestamp evidence alone does not establish immutable historical availability. Only the 8.1 MB compressed member is fetched via standard HTTP Range, not the 3.5 GB archive. CSV is cached locally (~20.5 MB); cached retrieval has no live server timestamp. CC BY 3.0 IGO attribution applies.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('iso3')
    p.add_argument('start', type=int)
    p.add_argument('end', type=int)
    a = p.parse_args()
    print(json.dumps(query(a.iso3, a.start, a.end), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
