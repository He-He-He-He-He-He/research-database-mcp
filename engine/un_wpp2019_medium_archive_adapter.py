"""UN WPP 2019 medium projection, archived period and population files."""
import release_runtime
import argparse, csv, hashlib, io, json, os, tempfile, zipfile
from pathlib import Path
import requests
URL = 'https://population.un.org/wpp/assets/Excel%20Files/5_Archive/WPP2019-CSV-data.zip'
CATALOG = 'https://population.un.org/wpp/assets/downloads.json'
SIZE = 271236186
BLOCK = 1048576
CACHE = release_runtime.home() / '.cache' / 'zju-research-toolkit'
MEMBERS = {'period': ('WPP2019_Period_Indicators_Medium.csv', 2531232, 847797, 'ad9e049ae8f00500c4a9f72224ab87d8001c9ae1014ad60aaf7b17450071aee8'), 'population': ('WPP2019_TotalPopulationBySex.csv', 22383021, 6001415, '9f4f4d097351846f788d0c0a069dd3ae164f49aad9c92a8f149e45311bf4b67f')}

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

def _fetch(kind):
    name, size, compressed, sha = MEMBERS[kind]
    path = CACHE / name
    if path.is_file() and path.stat().st_size == size and (hashlib.sha256(path.read_bytes()).hexdigest() == sha):
        return path
    if path.exists():
        raise ValueError('existing cache checksum differs; review manually')
    CACHE.mkdir(parents=True, exist_ok=True)
    tmp = None
    try:
        with RangeFile() as f, zipfile.ZipFile(f) as z:
            info = z.getinfo(name)
            if info.file_size != size or info.compress_size != compressed:
                raise ValueError('archive member changed')
            with tempfile.NamedTemporaryFile(dir=CACHE, prefix='.wpp2019-', delete=False) as dest:
                tmp = Path(dest.name)
                with z.open(info) as source:
                    while True:
                        chunk = source.read(262144)
                        if not chunk:
                            break
                        dest.write(chunk)
        if hashlib.sha256(tmp.read_bytes()).hexdigest() != sha:
            raise ValueError('member checksum changed')
        os.replace(tmp, path)
        return path
    finally:
        if tmp and tmp.exists():
            tmp.unlink()

def query(location, kind, start, end):
    if not isinstance(location, str) or not location.strip() or len(location) > 100 or (kind not in MEMBERS) or any((type(v) is not int for v in (start, end))) or (not 1950 <= start <= end <= 2100):
        raise ValueError('invalid query')
    path = _fetch(kind)
    out = []
    with path.open(encoding='utf-8-sig', newline='') as f:
        for r in csv.DictReader(f):
            if r['Variant'] != 'Medium' or location.strip().casefold() not in (r['Location'].casefold(), r['LocID'].casefold()):
                continue
            years = r['Time'].split('-')
            if not all((y.isdigit() for y in years)):
                continue
            if int(years[0]) <= end and (int(years[-1]) >= start if len(years) == 1 else int(years[-1]) > start):
                keys = ('LocID', 'Location', 'Variant', 'Time', 'MidPeriod', 'PopMale', 'PopFemale', 'PopTotal', 'PopDensity') if kind == 'population' else ('LocID', 'Location', 'Variant', 'Time', 'MidPeriod', 'TFR', 'LEx', 'LExMale', 'LExFemale', 'CBR', 'IMR', 'GrowthRate')
                out.append({k: r[k] for k in keys})
    return {'source_archive': URL, 'official_catalog': CATALOG, 'member': MEMBERS[kind][0], 'member_sha256': MEMBERS[kind][3], 'edition': '2019 revision, medium variant', 'kind': kind, 'records': out, 'note': 'UN WPP 2019 model estimates and medium projections, not census observations. Period indicators refer to five-year half-open intervals [start,end), not annual observations; 2020 onwards population is projected in this edition. Population numbers are thousands, TFR births per woman, life expectancy years; other units require source definitions. Period member ZIP timestamp 2020-03-04, population member 2020-03-06, archive HTTP Last-Modified observed 2024-12-13; timestamps do not independently prove immutability. Member is retrieved by standard HTTP Range and checksum pinned; cached locally. CC BY 3.0 IGO attribution applies.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('location')
    p.add_argument('kind', choices=list(MEMBERS))
    p.add_argument('start', type=int)
    p.add_argument('end', type=int)
    a = p.parse_args()
    print(json.dumps(query(a.location, a.kind, a.start, a.end), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
