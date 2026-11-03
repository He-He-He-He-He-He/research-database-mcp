"""UNODC World Drug Report 2026: national drug use prevalence observations."""
import release_runtime
import argparse, io, json, re, requests, openpyxl
URL = 'https://www.unodc.org/documents/data-and-analysis/WDR_2026/Annex/1.2_prevalence_of_drug_use_in_the_general_population_national_data.xlsx'
INDEX = 'https://www.unodc.org/unodc/en/data-and-analysis/world-drug-report-2026-annex.html'
METHOD = 'https://data.unodc.org/sites/dataportal.unodc.org/files/2026-07/metadata_drug_use_and_treatment.pdf'
SHEETS = ('Cannabis', 'Cocaine', 'Amphetamines', 'Ecstasy', 'Prescription Stimulants', 'Opioids', 'Opiates', 'Prescription opioids')
HEAD = ('Region', 'Sub-region', 'Country/Territory', 'Best', 'Low', 'High', 'Male', 'Female', 'Year', 'Age', 'Source', 'Method', 'Adjustment/\n notes', 'Specific notes')

def query(country, substance, start, end, local_file=None):
    if not isinstance(country, str) or not country.strip() or len(country) > 150:
        raise ValueError('invalid country')
    if substance not in SHEETS:
        raise ValueError('unsupported substance')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start, end))) or not 1900 <= start <= end <= 2100:
        raise ValueError('invalid years')
    if local_file:
        w = openpyxl.load_workbook(local_file, read_only=True, data_only=True)
    else:
        with requests.get(URL, stream=True, timeout=50) as r:
            r.raise_for_status()
            b = bytearray()
            for chunk in r.iter_content(65536):
                b.extend(chunk)
                if len(b) > 8000000:
                    raise ValueError('unexpected workbook size')
        w = openpyxl.load_workbook(io.BytesIO(b), read_only=True, data_only=True)
    try:
        s = w[substance]
        headers = next(s.iter_rows(min_row=3, max_row=3, min_col=2, max_col=15, values_only=True))
        if tuple(headers) != HEAD:
            raise ValueError('unexpected sheet structure')
        region = subregion = None
        out = []
        notes = []
        for vals in s.iter_rows(min_row=4, min_col=2, max_col=15, values_only=True):
            row = dict(zip(HEAD, vals))
            if isinstance(row['Region'], str) and ('UNODC Adjustments:' in row['Region'] or 'Method: HHS' in row['Region']):
                notes.append(row['Region'])
            if row['Region'] is not None:
                region = row['Region']
                subregion = None
            if row['Sub-region'] is not None:
                subregion = row['Sub-region']
            year = row['Year']
            if str(row['Country/Territory'] or '').casefold() != country.strip().casefold() or isinstance(year, bool) or (not isinstance(year, int)) or (not start <= year <= end):
                continue
            row['Region'] = region
            row['Sub-region'] = subregion
            out.append(row)
        return {'publisher': None if local_file else 'UNODC', 'source': local_file if local_file else URL, 'index': INDEX, 'methodology': METHOD, 'dataset': None if local_file else 'World Drug Report 2026 statistical annex 1.2', 'substance': substance, 'country': country, 'unit': None if local_file else 'percent of specified population; annual unless original notes indicate otherwise', 'records': out, 'source_notes': notes, 'note': 'Default age 15–64 unless the Age field specifies otherwise. Retain source, method and adjustment notes; national survey definitions and years differ, so results are not automatically comparable. Historical observations, not live estimates.' + (' Local workbook provenance, edition and measurement conventions are unverified.' if local_file else '')}
    finally:
        w.close()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('country')
    p.add_argument('substance', choices=SHEETS)
    p.add_argument('start', type=int)
    p.add_argument('end', type=int)
    p.add_argument('--local-file')
    a = p.parse_args()
    print(json.dumps(query(a.country, a.substance, a.start, a.end, a.local_file), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
