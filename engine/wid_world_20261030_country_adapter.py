"""WID.world country data and metadata in the 2026-10-30 public archive."""
import release_runtime
import argparse, csv, hashlib, io, json, re, zipfile
import requests
URL = 'https://wid.world/bulk_download/wid_all_data.zip'
PAGE = 'https://wid.world/data/'
SIZE = 886891414
ETAG = '"34dce396-65f0d42105bfc"'
LAST = 'Fri, 30 Oct 2026 11:40:07 GMT'
BLOCK = 1048576

class RangeFile(io.RawIOBase):

    def __init__(self):
        self.pos = 0
        self.blocks = {}
        self.session = requests.Session()

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
        if n > 30000000:
            raise ValueError('range request too large')
        out = bytearray()
        while n:
            idx = self.pos // BLOCK
            a = idx * BLOCK
            b = min(SIZE - 1, a + BLOCK - 1)
            if idx not in self.blocks:
                if len(self.blocks) >= 30:
                    raise ValueError('download budget exceeded')
                r = self.session.get(URL, headers={'Range': f'bytes={a}-{b}', 'If-Range': ETAG}, timeout=40)
                r.raise_for_status()
                if r.status_code != 206 or r.headers.get('Content-Range') != f'bytes {a}-{b}/{SIZE}' or len(r.content) != b - a + 1 or (r.headers.get('ETag') != ETAG):
                    raise ValueError('archive changed or range unsupported; review version')
                self.blocks[idx] = r.content
            block = self.blocks[idx]
            off = self.pos - a
            k = min(n, len(block) - off)
            out.extend(block[off:off + k])
            self.pos += k
            n -= k
        return bytes(out)

    def close(self):
        self.session.close()
        super().close()

def _member(z, name):
    info = z.getinfo(name)
    if info.file_size > 40000000 or info.compress_size > 15000000:
        raise ValueError('member too large')
    raw = z.read(info)
    return (raw, {'member': name, 'member_sha256': hashlib.sha256(raw).hexdigest(), 'member_timestamp': list(info.date_time), 'uncompressed_bytes': info.file_size, 'compressed_bytes': info.compress_size})

def query(country, variable, percentile='', start=2020, end=2025, limit=50):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{2}', country) or (not isinstance(variable, str)) or (not re.fullmatch('[a-z0-9]{4,24}', variable)) or (not isinstance(percentile, str)) or (len(percentile) > 20) or any((type(i) is not int for i in (start, end, limit))) or (not 1800 <= start <= end <= 2100) or (not 1 <= limit <= 200):
        raise ValueError('invalid country, variable, percentile, years or limit')
    with RangeFile() as f, zipfile.ZipFile(f) as z:
        d, di = _member(z, f'WID_data_{country}.csv')
        m, mi = _member(z, f'WID_metadata_{country}.csv')
    metadata = [r for r in csv.DictReader(io.StringIO(m.decode('utf-8-sig')), delimiter=';') if r['variable'] == variable]
    records = []
    count = 0
    for r in csv.DictReader(io.StringIO(d.decode('utf-8-sig')), delimiter=';'):
        if r['variable'] == variable and (not percentile or r['percentile'] == percentile) and r['year'].isdigit() and (start <= int(r['year']) <= end):
            count += 1
            if len(records) < limit:
                records.append(r)
    return {'source_archive': URL, 'source_page': PAGE, 'archive_size': SIZE, 'archive_etag': ETAG, 'archive_last_modified': LAST, 'data_member': di, 'metadata_member': mi, 'country': country, 'variable': variable, 'percentile_filter': percentile or None, 'matches': count, 'results': records, 'variable_metadata': metadata, 'quality_documentation': 'https://wid.world/data-quality/', 'note': 'WID.world is a research database distinct from UNU-WIDER WIID, not a government census. Archive version last modified 2026-10-30, and is not evidence of values available at a historical cutoff such as 2025-06-30; historical years can be revised or modeled. Values and data_quality are original strings; quality-grade interpretation depends on the variable category, see quality_documentation; preserve percentile, adult population/age, units, methodology, source and quality. Percentile p90p100 is top 10 percent, not average per person. Empty or missing is not zero. Data and metadata are selectively read from the official large ZIP using verified HTTP ranges; no full archive download or persistent cache.'}

def variables(country, keyword='', limit=50, offset=0):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{2}', country) or (not isinstance(keyword, str)) or (len(keyword) > 100) or any((type(i) is not int for i in (limit, offset))) or (not 1 <= limit <= 200) or (offset < 0):
        raise ValueError('invalid country, keyword, limit or offset')
    with RangeFile() as f, zipfile.ZipFile(f) as z:
        raw, info = _member(z, f'WID_metadata_{country}.csv')
    records = []
    count = 0
    for row in csv.DictReader(io.StringIO(raw.decode('utf-8-sig')), delimiter=';'):
        if not keyword or any((keyword.casefold() in str(row.get(k, '')).casefold() for k in ('variable', 'shortname', 'simpledes', 'technicaldes'))):
            count += 1
            if offset < count <= offset + limit:
                records.append(row)
    return {'source_archive': URL, 'source_page': PAGE, 'archive_last_modified': LAST, 'archive_etag': ETAG, 'metadata_member': info, 'country': country, 'keyword': keyword, 'matches': count, 'offset': offset, 'results': records, 'note': 'WID.world 2026-10-30 research archive is not a historical snapshot before 2025-06-30, not a government census, and not UNU-WIDER WIID. Read the original source, unit, age, population, method and quality description for each variable; present-day estimates may revise earlier years. Search is substring over code and descriptions, not a guarantee that every year or percentile exists. Current archive version is pinned; no full archive download.'}

def countries(keyword='', limit=50, offset=0):
    if not isinstance(keyword, str) or len(keyword) > 100 or any((type(i) is not int for i in (limit, offset))) or (not 1 <= limit <= 200) or (offset < 0):
        raise ValueError('invalid keyword, limit or offset')
    with RangeFile() as f, zipfile.ZipFile(f) as z:
        raw, info = _member(z, 'WID_countries.csv')
    rows = [r for r in csv.DictReader(io.StringIO(raw.decode('utf-8-sig')), delimiter=';') if not keyword or any((keyword.casefold() in str(v).casefold() for v in r.values()))]
    return {'source_archive': URL, 'source_page': PAGE, 'archive_last_modified': LAST, 'archive_etag': ETAG, 'member': info, 'keyword': keyword, 'matches': len(rows), 'offset': offset, 'results': rows[offset:offset + limit], 'note': 'WID.world country and region names/codes in the 2026-10-30 research archive, not a historical snapshot before 2025-06-30 or a legal designation. Presence in this list does not guarantee a particular variable or year exists. Names, regional groupings and codes are original and unchanged.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('country')
    p.add_argument('variable')
    p.add_argument('--percentile', default='')
    p.add_argument('--start', type=int, default=2020)
    p.add_argument('--end', type=int, default=2025)
    p.add_argument('--limit', type=int, default=50)
    a = p.parse_args()
    print(json.dumps(query(a.country, a.variable, a.percentile, a.start, a.end, a.limit), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
