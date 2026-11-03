"""UNODC global trafficking in persons 2025 workbook, original dimensions retained."""
import release_runtime
import argparse, json, os, re, openpyxl, requests
URL = 'https://data.unodc.org/sites/dataportal.unodc.org/files/2025-11/data_glotip.xlsx'
SHEET = 'data_glotip_1'
HEADERS = ['Iso3_code', 'Country', 'Region', 'Subregion', 'Indicator', 'Dimension', 'Category', 'Sex', 'Age', 'Year', 'Unit of measurement', 'txtVALUE', 'Source']

def download(path):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 384)
    try:
        with os.fdopen(fd, 'wb') as f, requests.get(URL, timeout=90, stream=True) as r:
            r.raise_for_status()
            n = 0
            for b in r.iter_content(65536):
                n += len(b)
                if n > 20000000:
                    raise ValueError('download exceeds 20 MB')
                f.write(b)
        w = openpyxl.load_workbook(path, read_only=True, data_only=True)
        try:
            if SHEET not in w.sheetnames:
                raise ValueError('unexpected workbook')
        finally:
            w.close()
        return {'source': URL, 'file': os.path.abspath(path), 'bytes': n}
    except BaseException:
        os.unlink(path)
        raise

def observations(path, country, start, end, indicator=None, dimension=None, category=None, sex=None, age=None, unit=None, limit=100):
    if not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('country must be ISO3')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start, end))) or not 1900 <= start <= end <= 2100:
        raise ValueError('invalid year range')
    if not 1 <= limit <= 1000:
        raise ValueError('limit must be 1..1000')
    filters = {'Indicator': indicator, 'Dimension': dimension, 'Category': category, 'Sex': sex, 'Age': age, 'Unit of measurement': unit}
    if any((v is not None and (not isinstance(v, str) or len(v) > 120) for v in filters.values())):
        raise ValueError('invalid filter')
    w = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        s = w[SHEET]
        s.reset_dimensions()
        head = list(next(s.iter_rows(min_row=3, max_row=3, values_only=True)))
        if head != HEADERS:
            raise ValueError('unexpected columns')
        out = []
        count = 0
        for v in s.iter_rows(min_row=4, values_only=True):
            x = dict(zip(head, v))
            y = x['Year']
            if x['Iso3_code'] != country or not isinstance(y, int) or (not start <= y <= end):
                continue
            if any((t is not None and str(x[k]).casefold() != t.casefold() for k, t in filters.items())):
                continue
            count += 1
            if len(out) < limit:
                out.append(x)
        return {'provider': None, 'source': os.path.abspath(path), 'dataset': None, 'expected_dataset': 'Trafficking in persons 2025 workbook', 'file': os.path.abspath(path), 'matched_count': count, 'returned_count': len(out), 'records': out, 'note': 'Detected victims are not total prevalence; suppression strings must be preserved; retain every dimension and source. Local workbook provenance, version and interpretation are unverified; expected_dataset describes the template only.'}
    finally:
        w.close()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    d = s.add_parser('download')
    d.add_argument('path')
    q = s.add_parser('data')
    q.add_argument('path')
    q.add_argument('country')
    q.add_argument('start', type=int)
    q.add_argument('end', type=int)
    q.add_argument('--indicator')
    q.add_argument('--dimension')
    q.add_argument('--category')
    q.add_argument('--sex')
    q.add_argument('--age')
    q.add_argument('--unit')
    q.add_argument('--limit', type=int, default=100)
    a = p.parse_args()
    result = download(a.path) if a.cmd == 'download' else observations(a.path, a.country, a.start, a.end, a.indicator, a.dimension, a.category, a.sex, a.age, a.unit, a.limit)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
