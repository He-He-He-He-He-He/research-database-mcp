"""European Commission JRC EDGAR 2026 greenhouse gas report workbook."""
import release_runtime
import argparse, io, json, re
import openpyxl, requests
URL = 'https://edgar.jrc.ec.europa.eu/booklet/EDGAR_2026_GHG_booklet_2026.xlsx'
SHEETS = ['GHG_totals_by_country', 'GHG_by_sector_and_country', 'GHG_per_GDP_by_country', 'GHG_per_capita_by_country', 'LULUCF_macroregions', 'LULUCF_countries']

def load():
    s = requests.Session()
    s.trust_env = False
    with s.get(URL, timeout=45, stream=True) as r:
        r.raise_for_status()
        b = bytearray()
        for chunk in r.iter_content(65536):
            b.extend(chunk)
            if len(b) > 10000000:
                raise ValueError('Workbook exceeds 10 MB')
    return openpyxl.load_workbook(io.BytesIO(b), read_only=True, data_only=True)

def metadata():
    w = load()
    try:
        return {'source': URL, 'sheets': w.sheetnames, 'info': [r[0] for r in w['info'].iter_rows(values_only=True) if r and r[0]], 'citations_and_conditions': [r[0] for r in w['Citations and references'].iter_rows(values_only=True) if r and r[0]]}
    finally:
        w.close()

def data(sheet, country='', year=None, substance='', sector='', limit=100):
    if sheet not in SHEETS or not 1 <= limit <= 1000:
        raise ValueError('Invalid sheet or limit')
    if country and (not re.fullmatch('[A-Za-z0-9 -]{2,40}', country)):
        raise ValueError('Invalid country')
    w = load()
    try:
        it = w[sheet].iter_rows(values_only=True)
        headers = list(next(it))
        out = []
        count = 0
        if year is not None and year not in headers:
            raise ValueError('Year absent from sheet')
        for row in it:
            rec = dict(zip(headers, row))
            code = str(rec.get('EDGAR Country Code', ''))
            name = str(rec.get('Country', ''))
            if country and country.casefold() not in (code.casefold(), name.casefold()):
                continue
            if substance and str(rec.get('Substance', '')).casefold() != substance.casefold():
                continue
            if sector and str(rec.get('Sector', '')).casefold() != sector.casefold():
                continue
            count += 1
            if len(out) < limit:
                if year is not None:
                    rec = {k: v for k, v in rec.items() if not isinstance(k, int) or k == year}
                out.append(rec)
        return {'source': URL, 'sheet': sheet, 'matches': count, 'returned': len(out), 'truncated': count > limit, 'rows': out, 'note': 'EDGAR estimates, not national inventory submissions. Check workbook info and conditions; IEA-derived fossil CO2 has separate CC BY-NC-ND restrictions.'}
    finally:
        w.close()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='command', required=True)
    s.add_parser('metadata')
    d = s.add_parser('data')
    d.add_argument('sheet', choices=SHEETS)
    d.add_argument('--country', default='')
    d.add_argument('--year', type=int)
    d.add_argument('--substance', default='')
    d.add_argument('--sector', default='')
    d.add_argument('--limit', type=int, default=100)
    a = p.parse_args()
    res = metadata() if a.command == 'metadata' else data(a.sheet, a.country, a.year, a.substance, a.sector, a.limit)
    print(json.dumps(res, ensure_ascii=False, indent=2, default=str))
if __name__ == '__main__':
    main()
