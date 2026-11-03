"""World Inequality Database country and variable retrieval from official public bulk ZIP."""
import release_runtime
import argparse, csv, io, json, re, zipfile, urllib.request, ssl, os
URL = 'https://wid.world/bulk_download/wid_all_data.zip'
DOCS = 'https://wid.world/codes-dictionary/'

class RangeFile(io.RawIOBase):
    """Seekable, bounded HTTP range reader for a stable public ZIP object."""
    CHUNK = 1024 * 1024
    LIMIT = 25 * 1024 * 1024

    def __init__(self, url):
        self.url = url
        self.tls = ssl.create_default_context()
        if os.path.isfile('/etc/ssl/cert.pem'):
            self.tls.load_verify_locations(cafile='/etc/ssl/cert.pem')
        with urllib.request.urlopen(urllib.request.Request(url, method='HEAD'), timeout=30, context=self.tls) as r:
            self.size = int(r.headers.get('Content-Length', '0'))
            self.etag = r.headers.get('ETag')
            accept = r.headers.get('Accept-Ranges', '')
        if self.size <= 0 or not self.etag or accept.lower() != 'bytes':
            raise RuntimeError('server does not advertise stable range access')
        self.pos = 0
        self.cache = {}
        self.downloaded = 0

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, offset, whence=0):
        p = offset if whence == 0 else self.pos + offset if whence == 1 else self.size + offset if whence == 2 else -1
        if p < 0:
            raise ValueError('negative offset')
        self.pos = p
        return p

    def read(self, n=-1):
        if n is None or n < 0:
            n = self.size - self.pos
        n = min(n, max(0, self.size - self.pos))
        out = []
        while n:
            idx = self.pos // self.CHUNK
            if idx not in self.cache:
                a = idx * self.CHUNK
                b = min(a + self.CHUNK, self.size) - 1
                if self.downloaded + b - a + 1 > self.LIMIT:
                    raise ValueError('range download budget exceeded')
                request = urllib.request.Request(self.url, headers={'Range': f'bytes={a}-{b}', 'If-Match': self.etag})
                with urllib.request.urlopen(request, timeout=60, context=self.tls) as r:
                    if r.status != 206 or r.headers.get('Content-Range') != f'bytes {a}-{b}/{self.size}':
                        raise RuntimeError('server returned inconsistent range or changed ZIP')
                    data = r.read(b - a + 2)
                    if len(data) != b - a + 1:
                        raise RuntimeError('incomplete or oversized range response')
                    self.cache[idx] = data
                    self.downloaded += len(data)
            chunk = self.cache[idx]
            at = self.pos % self.CHUNK
            take = min(n, len(chunk) - at)
            if take <= 0:
                raise RuntimeError('invalid range chunk')
            out.append(chunk[at:at + take])
            self.pos += take
            n -= take
        return b''.join(out)

def query(country, variable, percentile, start, end, limit=200):
    if not re.fullmatch('[A-Z]{2}', country) or not re.fullmatch('[a-z0-9]{6,20}', variable) or (not re.fullmatch('p\\d+(?:\\.\\d+)?p\\d+(?:\\.\\d+)?', percentile)):
        raise ValueError('invalid country, variable or percentile')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start, end, limit))) or not 1800 <= start <= end <= 2100 or (not 1 <= limit <= 500):
        raise ValueError('invalid year or limit')
    rows = []
    metadata = []
    count = 0
    with RangeFile(URL) as source, zipfile.ZipFile(source) as z:
        for entry in (f'WID_metadata_{country}.csv', f'WID_data_{country}.csv'):
            info = z.getinfo(entry)
            if info.file_size > 100000000 or info.compress_size > 20000000:
                raise ValueError('country member too large')
            with z.open(info) as raw, io.TextIOWrapper(raw, encoding='utf-8-sig', newline='') as f:
                reader = csv.DictReader(f, delimiter=';')
                if not {'country', 'variable'}.issubset(reader.fieldnames or []):
                    raise ValueError('unexpected member schema')
                if entry.startswith('WID_metadata_'):
                    for r in reader:
                        if r['country'] == country and r['variable'] == variable:
                            metadata.append(r)
                else:
                    if not {'percentile', 'year', 'value', 'age', 'pop', 'data_quality'}.issubset(reader.fieldnames or []):
                        raise ValueError('unexpected data schema')
                    for r in reader:
                        if r['country'] != country or r['variable'] != variable or r['percentile'] != percentile or (not r['year'].isdigit()) or (not start <= int(r['year']) <= end):
                            continue
                        count += 1
                        if len(rows) < limit:
                            rows.append(r)
    if not metadata:
        raise ValueError('no matching country-variable metadata')
    return {'provider': 'World Inequality Database (research consortium)', 'source': URL, 'code_dictionary': DOCS, 'country': country, 'variable': variable, 'percentile': percentile, 'metadata': metadata, 'matched_count': count, 'records': rows, 'note': 'Country member and its metadata are retrieved by HTTP range from official large ZIP, not the whole archive. Preserve age, population, unit, quality, source and method; values may combine survey, tax, model and extrapolation. Countries and years may not be directly comparable; not official national statistical releases. Repeated annual values or low quality flags can indicate extrapolation or sparse evidence, but do not prove extrapolation; consult source metadata.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('country')
    p.add_argument('variable')
    p.add_argument('percentile')
    p.add_argument('start', type=int)
    p.add_argument('end', type=int)
    p.add_argument('--limit', type=int, default=200)
    a = p.parse_args()
    print(json.dumps(query(a.country, a.variable, a.percentile, a.start, a.end, a.limit), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
