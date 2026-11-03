"""UNODC World Drug Report 2026 annex: drug seizures 2015–2024."""
import release_runtime
import argparse, io, json, re, requests, openpyxl
URL = 'https://www.unodc.org/documents/data-and-analysis/WDR_2026/Annex/7.1_Drug_seizures_2015-2024.xlsx'
INDEX = 'https://www.unodc.org/unodc/en/data-and-analysis/world-drug-report-2026-annex.html'
HEAD = ('Iso3_code', 'Region', 'SubRegion', 'Country', 'DrugGroup', 'DrugSubGroup', 'DrugName', 'Reference year', 'Kilograms', 'Source', 'Footnote')

def query(country, start, end, drug='', offset=0, limit=100, local_file=None):
    if not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('country must be ISO3')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start, end, offset, limit))) or not 2015 <= start <= end <= 2024 or offset < 0 or (not 1 <= limit <= 500):
        raise ValueError('invalid bounds')
    if not isinstance(drug, str) or len(drug) > 150:
        raise ValueError('invalid drug filter')
    if local_file:
        w = openpyxl.load_workbook(local_file, read_only=True, data_only=True)
    else:
        with requests.get(URL, stream=True, timeout=45) as r:
            r.raise_for_status()
            buf = bytearray()
            for b in r.iter_content(65536):
                buf.extend(b)
                if len(buf) > 8000000:
                    raise ValueError('unexpected workbook size')
        w = openpyxl.load_workbook(io.BytesIO(buf), read_only=True, data_only=True)
    try:
        s = w['Seizures']
        h = next(s.iter_rows(min_row=2, max_row=2, max_col=11, values_only=True))
        if tuple(h) != HEAD:
            raise ValueError('unexpected workbook schema')
        out = []
        count = 0
        for vals in s.iter_rows(min_row=3, max_col=11, values_only=True):
            row = dict(zip(HEAD, vals))
            y = row['Reference year']
            if row['Iso3_code'] != country or isinstance(y, bool) or (not isinstance(y, int)) or (not start <= y <= end):
                continue
            if drug.casefold() not in ' '.join((str(row[k] or '') for k in ('DrugGroup', 'DrugSubGroup', 'DrugName'))).casefold():
                continue
            if offset <= count < offset + limit:
                out.append(row)
            count += 1
        return {'publisher': None if local_file else 'UNODC', 'source': local_file if local_file else URL, 'index': INDEX, 'country': country, 'years': [start, end], 'drug_filter': drug, 'matched_count': count, 'offset': offset, 'records': out, 'unit': 'kilograms', 'note': 'Recorded seizures from national or other named sources, not estimated production, consumption or total trafficking. Preserve source, substance and footnote; reporting coverage and methodology vary.' + (' Local workbook provenance, edition and measurement conventions are unverified.' if local_file else '')}
    finally:
        w.close()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('country')
    p.add_argument('start', type=int)
    p.add_argument('end', type=int)
    p.add_argument('--drug', default='')
    p.add_argument('--offset', type=int, default=0)
    p.add_argument('--limit', type=int, default=100)
    p.add_argument('--local-file')
    a = p.parse_args()
    print(json.dumps(query(a.country, a.start, a.end, a.drug, a.offset, a.limit, a.local_file), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
