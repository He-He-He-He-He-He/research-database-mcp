"""U.S. Census International Database official bulk ZIP, streamed locally."""
import release_runtime
import argparse, csv, io, json, os, re, tempfile, zipfile
from pathlib import Path
import requests
URL = 'https://www.census.gov/data-tools/demo/data/idb/dataset/idbzip.zip'
API = 'https://api.census.gov/data/timeseries/idb/5year/variables.json'
MAXZIP = 120000000

def fetch(dest):
    target = release_runtime.expandpath(Path(dest))
    if target.exists():
        raise FileExistsError('Destination exists; choose a new filename')
    target.parent.mkdir(parents=True, exist_ok=True)
    s = requests.Session()
    s.trust_env = False
    fd, tmp = tempfile.mkstemp(prefix='.idb-download-', dir=target.parent)
    try:
        with os.fdopen(fd, 'wb') as f, s.get(URL, timeout=90, stream=True) as r:
            r.raise_for_status()
            n = 0
            for chunk in r.iter_content(262144):
                n += len(chunk)
                if n > MAXZIP:
                    raise ValueError('Download exceeds 120 MB')
                f.write(chunk)
        with zipfile.ZipFile(tmp) as z:
            if not {'readme.txt', 'idb5yr.txt', 'idbsingleyear.txt'}.issubset(z.namelist()):
                raise ValueError('Unexpected archive contents')
        os.link(tmp, target)
        return {'source': URL, 'archive': str(target.resolve()), 'bytes': n}
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

def metadata(archive):
    with zipfile.ZipFile(archive) as z:
        info = {x.filename: {'uncompressed_bytes': x.file_size, 'compressed_bytes': x.compress_size} for x in z.infolist()}
        return {'archive': str(Path(archive).resolve()), 'source': str(Path(archive).resolve()), 'reference_source': URL, 'provenance_note': 'Local archive provenance and version unverified.', 'readme': z.read('readme.txt').decode('utf-8-sig'), 'members': info, 'variable_definitions': API}

def data(archive, table, geo, year, fields, limit):
    if table not in ['5year', 'singleyear'] or not re.fullmatch('[A-Z0-9]{5,40}', geo):
        raise ValueError('Invalid table or GEO_ID')
    if not 1800 <= year <= 2100 or not 1 <= limit <= 1000:
        raise ValueError('Invalid year or limit')
    filename = 'idb5yr.txt' if table == '5year' else 'idbsingleyear.txt'
    rows = []
    count = 0
    with zipfile.ZipFile(archive) as z:
        info = z.getinfo(filename)
        if info.file_size > 300000000:
            raise ValueError('Archive member exceeds 300 MB')
        with z.open(info) as raw:
            reader = csv.DictReader(io.TextIOWrapper(raw, encoding='utf-8-sig'), delimiter='|')
            available = reader.fieldnames or []
            cols = [f for f in fields.split(',') if f] if fields else available
            if not set(cols).issubset(set(available)):
                raise ValueError('Unknown field; inspect metadata and official variable list')
            for x in reader:
                if x.get('#YR') == str(year) and x.get('GEO_ID') == geo:
                    count += 1
                    if len(rows) < limit:
                        rows.append({k: x[k] for k in cols})
    return {'source': str(Path(archive).resolve()), 'reference_source': URL, 'archive': str(Path(archive).resolve()), 'table': filename, 'GEO_ID': geo, 'year': year, 'matches': count, 'returned': len(rows), 'truncated': count > limit, 'rows': rows, 'note': 'Local archive provenance and version are unverified; if it is the expected IDB file, values are estimates/projections, not local census results. GEO_ID must be verified against geography and variables.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    f = s.add_parser('download')
    f.add_argument('path')
    m = s.add_parser('metadata')
    m.add_argument('archive')
    d = s.add_parser('data')
    d.add_argument('archive')
    d.add_argument('--table', choices=['5year', 'singleyear'], default='5year')
    d.add_argument('--geo', required=True)
    d.add_argument('--year', type=int, required=True)
    d.add_argument('--fields', default='')
    d.add_argument('--limit', type=int, default=100)
    a = p.parse_args()
    result = fetch(a.path) if a.cmd == 'download' else metadata(a.archive) if a.cmd == 'metadata' else data(a.archive, a.table, a.geo, a.year, a.fields, a.limit)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
