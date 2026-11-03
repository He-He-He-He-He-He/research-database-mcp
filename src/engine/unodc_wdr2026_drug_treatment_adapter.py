"""UNODC WDR 2026: persons treated by primary drug of use, 2020–2024."""
import release_runtime
import argparse, io, json, re, openpyxl, requests
URL = 'https://www.unodc.org/documents/data-and-analysis/WDR_2026/Annex/5.1_treatment_by_primary_drug_of_use.xlsx'
METHOD = 'https://data.unodc.org/sites/dataportal.unodc.org/files/2026-07/metadata_drug_use_and_treatment.pdf'
HEAD = ('Region', 'SubRegion', 'Country', 'msCode', 'Reference year', 'DrugGroup', 'Drug', 'Sex', 'value', 'Specify reference year', 'Coverage')

def query(country, start, end, drug='', sex='', offset=0, limit=100, local_file=None):
    if not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('country must be ISO3')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start, end, offset, limit))) or not 2020 <= start <= end <= 2024 or offset < 0 or (not 1 <= limit <= 500):
        raise ValueError('invalid bounds')
    if not isinstance(drug, str) or len(drug) > 150 or sex not in ('', 'Total', 'Females', 'Males'):
        raise ValueError('invalid filters')
    if local_file:
        w = openpyxl.load_workbook(local_file, read_only=True, data_only=True)
    else:
        with requests.get(URL, stream=True, timeout=45) as r:
            r.raise_for_status()
            data = bytearray()
            for b in r.iter_content(65536):
                data.extend(b)
                if len(data) > 5000000:
                    raise ValueError('unexpected workbook size')
        w = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    try:
        s = w['Sheet1']
        h = next(s.iter_rows(min_row=3, max_row=3, max_col=11, values_only=True))
        if tuple(h) != HEAD:
            raise ValueError('unexpected workbook schema')
        out = []
        total = 0
        for vals in s.iter_rows(min_row=4, max_col=11, values_only=True):
            row = dict(zip(HEAD, vals))
            year = row['Reference year']
            if row['msCode'] != country or isinstance(year, bool) or (not isinstance(year, int)) or (not start <= year <= end) or (sex and row['Sex'] != sex):
                continue
            if drug.casefold() not in ' '.join((str(row[k] or '') for k in ('DrugGroup', 'Drug'))).casefold():
                continue
            if offset <= total < offset + limit:
                out.append(row)
            total += 1
        return {'publisher': None if local_file else 'UNODC', 'source': local_file if local_file else URL, 'methodology': METHOD, 'dataset': None if local_file else 'World Drug Report 2026 annex 5.1', 'country': country, 'matched_count': total, 'offset': offset, 'records': out, 'unit': None if local_file else 'reported number of persons treated', 'note': 'Primary drug for which treatment sought; not the prevalence of drug use or number of all persons needing treatment. Coverage and reporting definitions vary. Any drug and drug-specific rows overlap; totals and sex rows also overlap.' + (' Local workbook provenance, edition and measurement conventions are unverified.' if local_file else '')}
    finally:
        w.close()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('country')
    p.add_argument('start', type=int)
    p.add_argument('end', type=int)
    p.add_argument('--drug', default='')
    p.add_argument('--sex', choices=['', 'Total', 'Females', 'Males'], default='')
    p.add_argument('--offset', type=int, default=0)
    p.add_argument('--limit', type=int, default=100)
    p.add_argument('--local-file')
    a = p.parse_args()
    print(json.dumps(query(a.country, a.start, a.end, a.drug, a.sex, a.offset, a.limit, a.local_file), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
