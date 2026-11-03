"""WTO experimental TiSMoS 2019 release: services trade by supply mode."""
import release_runtime
import argparse, csv, io, json, os, re, zipfile, requests, openpyxl
BASE = 'https://www.wto.org/english/res_e/statis_e/daily_update_e/'
FILES = {'imports': ('Tismos_imports.zip', 'TISMOS_Imports.csv'), 'exports': ('Tismos_exports.zip', 'TISMOS_Exports.csv')}
CODEURL = BASE + 'Tismos_codes.xlsx'
MODE = {'M1': 'Cross-border supply', 'M2': 'Consumption abroad', 'M3': 'Commercial presence', 'M4': 'Presence of natural persons'}

def download(flow, path):
    if flow not in FILES:
        raise ValueError('invalid flow')
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 384)
    try:
        with os.fdopen(fd, 'wb') as f, requests.get(BASE + FILES[flow][0], timeout=90, stream=True) as r:
            r.raise_for_status()
            n = 0
            for b in r.iter_content(65536):
                n += len(b)
                if n > 15000000:
                    raise ValueError('download exceeds 15 MB')
                f.write(b)
        with zipfile.ZipFile(path) as z:
            validate(z, flow)
        return {'source': BASE + FILES[flow][0], 'file': os.path.abspath(path), 'bytes': n}
    except BaseException:
        os.unlink(path)
        raise

def validate(z, flow):
    name = FILES[flow][1]
    if z.namelist() != [name] or z.getinfo(name).file_size > 50000000:
        raise ValueError('unexpected WTO ZIP')

def codebook(kind, keyword=''):
    if kind not in {'countries', 'indicators', 'methodology'}:
        raise ValueError('invalid codebook')
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('invalid keyword')
    r = requests.get(CODEURL, timeout=30)
    r.raise_for_status()
    if len(r.content) > 1000000:
        raise ValueError('codebook too large')
    w = openpyxl.load_workbook(io.BytesIO(r.content), read_only=True, data_only=True)
    try:
        sheet = {'countries': 'Country Codes', 'indicators': 'Items and correspondence', 'methodology': 'Methodology Codes'}[kind]
        rows = [list(x) for x in w[sheet].iter_rows(min_row=2, values_only=True) if x[0] is not None and keyword.casefold() in ' '.join((str(v or '') for v in x)).casefold()]
        return {'source': CODEURL, 'kind': kind, 'matched_count': len(rows), 'records': rows}
    finally:
        w.close()

def observations(path, flow, reporter, indicator, start, end, mode=None, limit=100):
    if flow not in FILES:
        raise ValueError('invalid flow')
    if not re.fullmatch('[A-Z0-9]{2,4}', reporter) or not re.fullmatch('[A-Z0-9]{1,30}', indicator):
        raise ValueError('invalid reporter or indicator')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start, end))) or not 2005 <= start <= end <= 2017:
        raise ValueError('this release covers 2005–2017')
    if mode is not None and mode not in MODE:
        raise ValueError('invalid mode')
    if not 1 <= limit <= 1000:
        raise ValueError('invalid limit')
    out = []
    count = 0
    with zipfile.ZipFile(path) as z:
        validate(z, flow)
        with z.open(FILES[flow][1]) as f:
            r = csv.DictReader(io.TextIOWrapper(f, encoding='utf-8-sig', newline=''))
            if r.fieldnames != ['FLOW', 'REPORTER', 'PARTNER', 'INDICATOR', 'YEAR', 'MODE', 'VALUE', 'METH']:
                raise ValueError('unexpected CSV columns')
            for x in r:
                if x['REPORTER'] != reporter or x['INDICATOR'] != indicator or (not start <= int(x['YEAR']) <= end) or (mode and x['MODE'] != mode):
                    continue
                count += 1
                x['mode_description'] = MODE.get(x['MODE'])
                x['unit'] = None
                x['expected_unit'] = 'million US dollars if source identity is verified'
                x['VALUE'] = x['VALUE'] or None
                if len(out) < limit:
                    out.append(x)
    return {'provider': None, 'dataset': None, 'expected_dataset': 'TiSMoS experimental 2019 release', 'source': os.path.abspath(path), 'reference_source': BASE + FILES[flow][0], 'file': os.path.abspath(path), 'matched_count': count, 'records': out, 'note': 'Estimates and reported data; method codes are available in official codebook. Null is missing, not zero. Local archive provenance, edition, unit and interpretation are unverified.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    d = s.add_parser('download')
    d.add_argument('flow', choices=FILES)
    d.add_argument('path')
    c = s.add_parser('codes')
    c.add_argument('kind', choices=['countries', 'indicators', 'methodology'])
    c.add_argument('--keyword', default='')
    q = s.add_parser('data')
    q.add_argument('path')
    q.add_argument('flow', choices=FILES)
    q.add_argument('reporter')
    q.add_argument('indicator')
    q.add_argument('start', type=int)
    q.add_argument('end', type=int)
    q.add_argument('--mode', choices=MODE)
    q.add_argument('--limit', type=int, default=100)
    a = p.parse_args()
    result = download(a.flow, a.path) if a.cmd == 'download' else codebook(a.kind, a.keyword) if a.cmd == 'codes' else observations(a.path, a.flow, a.reporter, a.indicator, a.start, a.end, a.mode, a.limit)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
