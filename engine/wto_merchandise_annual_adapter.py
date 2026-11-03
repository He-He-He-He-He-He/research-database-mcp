"""WTO merchandise imports/exports by product group, annual bulk statistics."""
import release_runtime
import argparse, csv, io, json, os, re, zipfile, requests
URL = 'https://stats.wto.org/assets/UserGuide/merchandise_values_annual_dataset.zip'
MEMBER = 'merchandise_values_annual_dataset.csv'

def validate(z):
    if z.namelist() != [MEMBER] or z.getinfo(MEMBER).file_size > 150000000:
        raise ValueError('unexpected WTO ZIP')

def download(path):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 384)
    try:
        with os.fdopen(fd, 'wb') as f, requests.get(URL, timeout=90, stream=True) as r:
            r.raise_for_status()
            n = 0
            for b in r.iter_content(65536):
                n += len(b)
                if n > 20000000:
                    raise ValueError('file exceeds 20 MB')
                f.write(b)
        with zipfile.ZipFile(path) as z:
            validate(z)
        return {'source': URL, 'file': os.path.abspath(path), 'bytes': n}
    except BaseException:
        os.unlink(path)
        raise

def observations(path, reporter, start, end, product=None, flow=None, partner=None, limit=100):
    if not re.fullmatch('[A-Z0-9]{3}', reporter):
        raise ValueError('reporter must be 3-character code')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start, end))) or not 1900 <= start <= end <= 2100:
        raise ValueError('invalid year range')
    if flow not in (None, 'imports', 'exports'):
        raise ValueError('invalid flow')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 1000):
        raise ValueError('invalid limit')
    if any((v is not None and (not isinstance(v, str) or len(v) > 100) for v in (product, partner))):
        raise ValueError('invalid filter')
    out = []
    count = 0
    with zipfile.ZipFile(path) as z:
        validate(z)
        with z.open(MEMBER) as f:
            r = csv.DictReader(io.TextIOWrapper(f, encoding='cp1252', newline=''))
            expected = {'ReporterISO3A', 'ProductCode', 'Year', 'Value', 'IndicatorCode', 'Unit', 'Partner'}
            if not expected.issubset(r.fieldnames or []):
                raise ValueError('unexpected fields')
            for x in r:
                if x['ReporterISO3A'] != reporter or not start <= int(x['Year']) <= end:
                    continue
                if product and x['ProductCode'].casefold() != product.casefold():
                    continue
                if partner and x['Partner'].casefold() != partner.casefold():
                    continue
                if flow and x['IndicatorCode'] != ('ITS_MTV_AM' if flow == 'imports' else 'ITS_MTV_AX'):
                    continue
                count += 1
                if len(out) < limit:
                    out.append(x)
    return {'provider': None, 'source': os.path.abspath(path), 'reference_source': URL, 'file': os.path.abspath(path), 'matched_count': count, 'returned_count': len(out), 'records': out, 'note': 'Keep partner, product classification, flags and unit; empty value is not zero. Local archive provenance and edition are unverified.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    d = s.add_parser('download')
    d.add_argument('path')
    q = s.add_parser('data')
    q.add_argument('path')
    q.add_argument('reporter')
    q.add_argument('start', type=int)
    q.add_argument('end', type=int)
    q.add_argument('--product')
    q.add_argument('--flow', choices=['imports', 'exports'])
    q.add_argument('--partner')
    q.add_argument('--limit', type=int, default=100)
    a = p.parse_args()
    result = download(a.path) if a.cmd == 'download' else observations(a.path, a.reporter, a.start, a.end, a.product, a.flow, a.partner, a.limit)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
