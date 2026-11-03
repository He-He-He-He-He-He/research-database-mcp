"""EIA international energy series: explicit download and local bulk ZIP query."""
import release_runtime
import argparse, json, os, re, zipfile, requests
URL = 'https://www.eia.gov/opendata/bulk/INTL.zip'
MAX_ZIP = 100000000
MAX_TEXT = 300000000

def download(path):
    """Download to a new file; never overwrite an existing path."""
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 384)
    try:
        with os.fdopen(fd, 'wb') as f, requests.get(URL, timeout=120, stream=True) as r:
            r.raise_for_status()
            n = 0
            for chunk in r.iter_content(65536):
                n += len(chunk)
                if n > MAX_ZIP:
                    raise ValueError('download exceeds 100 MB')
                f.write(chunk)
        with zipfile.ZipFile(path) as z:
            if z.namelist() != ['INTL.txt'] or z.getinfo('INTL.txt').file_size > MAX_TEXT:
                raise ValueError('unexpected EIA ZIP')
        return {'source': URL, 'saved_to': os.path.abspath(path), 'bytes': n}
    except BaseException:
        os.unlink(path)
        raise

def search(path, keyword='', geography=None, frequency=None, series_id=None, start=None, end=None, limit=20):
    if not isinstance(keyword, str) or len(keyword) > 200:
        raise ValueError('invalid keyword')
    if not (keyword or geography or series_id):
        raise ValueError('supply a search filter')
    if geography and (not re.fullmatch('[A-Z0-9_-]{1,20}', geography)):
        raise ValueError('invalid geography')
    if frequency not in (None, 'A', 'M', 'Q'):
        raise ValueError('invalid frequency')
    if not 1 <= limit <= 100:
        raise ValueError('limit must be 1..100')
    if any((v is not None and (isinstance(v, bool) or not 1800 <= int(v) <= 2100) for v in (start, end))):
        raise ValueError('invalid years')
    if start is not None and end is not None and (start > end):
        raise ValueError('invalid range')
    found = []
    count = 0
    with zipfile.ZipFile(path) as z:
        if z.namelist() != ['INTL.txt'] or z.getinfo('INTL.txt').file_size > MAX_TEXT:
            raise ValueError('unexpected EIA ZIP')
        with z.open('INTL.txt') as f:
            for line in f:
                x = json.loads(line)
                if keyword.casefold() not in x.get('name', '').casefold():
                    continue
                if geography and x.get('geography') != geography:
                    continue
                if frequency and x.get('f') != frequency:
                    continue
                if series_id and x.get('series_id') != series_id:
                    continue
                count += 1
                if len(found) >= limit:
                    continue
                data = x.get('data', [])
                if start is not None:
                    data = [o for o in data if int(str(o[0])[:4]) >= start]
                if end is not None:
                    data = [o for o in data if int(str(o[0])[:4]) <= end]
                x['data'] = data
                found.append(x)
    return {'source': os.path.abspath(path), 'local_file': os.path.abspath(path), 'provider': None, 'matched_series': count, 'returned_series': len(found), 'series': found, 'note': 'Data and metadata retain source units; series names determine reporting geography and flows. Local archive provenance and version are unverified; compare the archive with the official download before attribution.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    d = s.add_parser('download')
    d.add_argument('path')
    q = s.add_parser('search')
    q.add_argument('path')
    q.add_argument('--keyword', default='')
    q.add_argument('--geography')
    q.add_argument('--frequency', choices=['A', 'M', 'Q'])
    q.add_argument('--series-id')
    q.add_argument('--start', type=int)
    q.add_argument('--end', type=int)
    q.add_argument('--limit', type=int, default=20)
    a = p.parse_args()
    result = download(a.path) if a.cmd == 'download' else search(a.path, a.keyword, a.geography, a.frequency, a.series_id, a.start, a.end, a.limit)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
