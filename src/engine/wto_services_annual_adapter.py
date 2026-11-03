"""WTO annual services trade bulk data; bounded streaming local search."""
import release_runtime
import argparse, csv, io, json, os, re, zipfile, requests
URL = 'https://stats.wto.org/assets/UserGuide/services_annual_dataset.zip'
MEMBER = 'services_annual_dataset.csv'

def validate(z):
    if z.namelist() != [MEMBER] or z.getinfo(MEMBER).file_size > 3500000000:
        raise ValueError('unexpected WTO ZIP')

def download(path):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 384)
    try:
        with os.fdopen(fd, 'wb') as f, requests.get(URL, timeout=240, stream=True) as r:
            r.raise_for_status()
            n = 0
            for b in r.iter_content(262144):
                n += len(b)
                if n > 120000000:
                    raise ValueError('file exceeds 120 MB')
                f.write(b)
        with zipfile.ZipFile(path) as z:
            validate(z)
        return {'source': URL, 'file': os.path.abspath(path), 'bytes': n}
    except BaseException:
        os.unlink(path)
        raise

def observations(path, reporter, year, product, flow=None, partner='World', limit=100, max_scan=10000000):
    if not re.fullmatch('[A-Z0-9]{3}', reporter):
        raise ValueError('reporter must be 3-character code')
    if isinstance(year, bool) or not isinstance(year, int) or (not 1900 <= year <= 2100):
        raise ValueError('invalid year')
    if not re.fullmatch('[A-Z0-9_]{1,30}', product):
        raise ValueError('invalid product code')
    if flow not in (None, 'imports', 'exports'):
        raise ValueError('invalid flow')
    if not isinstance(partner, str) or not 1 <= len(partner) <= 100:
        raise ValueError('invalid partner')
    if any((isinstance(v, bool) or not isinstance(v, int) for v in (limit, max_scan))) or not 1 <= limit <= 1000 or (not 1 <= max_scan <= 20000000):
        raise ValueError('invalid scan or result limit')
    out = []
    scanned = 0
    complete = True
    reason = None
    with zipfile.ZipFile(path) as z:
        validate(z)
        with z.open(MEMBER) as f:
            r = csv.DictReader(io.TextIOWrapper(f, encoding='cp1252', newline=''))
            expected = {'ReporterISO3A', 'ProductCode', 'Year', 'Value', 'IndicatorCode', 'Unit', 'Partner'}
            if not expected.issubset(r.fieldnames or []):
                raise ValueError('unexpected CSV columns')
            for x in r:
                if scanned >= max_scan:
                    complete = False
                    reason = 'scan_limit'
                    break
                scanned += 1
                if x['ReporterISO3A'] != reporter or x['Year'] != str(year) or x['ProductCode'] != product or (x['Partner'].casefold() != partner.casefold()):
                    continue
                if flow and x['IndicatorCode'] != ('ITS_CS_AM6' if flow == 'imports' else 'ITS_CS_AX6'):
                    continue
                out.append(x)
                if len(out) >= limit:
                    complete = False
                    reason = 'result_limit'
                    break
    return {'provider': None, 'source': os.path.abspath(path), 'reference_source': URL, 'file': os.path.abspath(path), 'scanned_rows': scanned, 'scan_complete': complete, 'stop_reason': reason, 'returned_count': len(out), 'records': out, 'note': 'Partial scan cannot establish total results or absence. Check product classification, unit and flag. Local archive provenance and edition are unverified.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    d = s.add_parser('download')
    d.add_argument('path')
    q = s.add_parser('data')
    q.add_argument('path')
    q.add_argument('reporter')
    q.add_argument('year', type=int)
    q.add_argument('product')
    q.add_argument('--flow', choices=['imports', 'exports'])
    q.add_argument('--partner', default='World')
    q.add_argument('--limit', type=int, default=100)
    q.add_argument('--max-scan', type=int, default=10000000)
    a = p.parse_args()
    result = download(a.path) if a.cmd == 'download' else observations(a.path, a.reporter, a.year, a.product, a.flow, a.partner, a.limit, a.max_scan)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
