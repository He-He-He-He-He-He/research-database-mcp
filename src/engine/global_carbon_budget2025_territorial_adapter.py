"""Global Carbon Budget 2025: territorial fossil CO2 and cement emissions."""
import release_runtime
import argparse, io, json, requests, openpyxl
URL = 'https://globalcarbonbudget.org/download/2345/?tmstv=1762815968'
META = 'https://globalcarbonbudget.org/datahub/the-latest-gcb-data-2025/'
DOI = 'https://doi.org/10.18160/gcp-2025'

def query(country, start, end, local_file=None):
    if not isinstance(country, str) or not country.strip() or len(country) > 100:
        raise ValueError('invalid country')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start, end))) or not 1850 <= start <= end <= 2024:
        raise ValueError('years must be 1850–2024')
    if local_file:
        w = openpyxl.load_workbook(local_file, read_only=True, data_only=True)
    else:
        with requests.get(URL, stream=True, timeout=45) as r:
            r.raise_for_status()
            b = bytearray()
            for x in r.iter_content(65536):
                b.extend(x)
                if len(b) > 5000000:
                    raise ValueError('unexpected workbook size')
        w = openpyxl.load_workbook(io.BytesIO(b), read_only=True, data_only=True)
    try:
        s = w['Territorial Emissions']
        head = next(s.iter_rows(min_row=12, max_row=12, values_only=True))
        matches = [i for i, x in enumerate(head) if isinstance(x, str) and x.casefold() == country.strip().casefold()]
        if len(matches) != 1:
            raise ValueError('country not found or ambiguous; use workbook name')
        col = matches[0]
        out = []
        for row in s.iter_rows(min_row=13, max_row=187, values_only=True):
            y = row[0]
            if isinstance(y, int) and start <= y <= end and isinstance(row[col], (int, float)):
                out.append({'year': y, 'value': row[col]})
        return {'publisher': None if local_file else 'Global Carbon Project (scientific collaboration)', 'dataset': None if local_file else 'Global Carbon Budget 2025 national territorial fossil carbon emissions', 'source': local_file if local_file else URL, 'metadata': META, 'data_doi': None if local_file else DOI, 'country': head[col], 'unit': 'million tonnes carbon per year (MtC/year)', 'records': out, 'note': 'Includes fossil fuel combustion and oxidation and cement production; excludes international aviation and shipping bunker fuels from national estimates. This is carbon mass, not CO2 mass; workbook gives 1 MtC = 3.664 MtCO2. Historical country disaggregations may be estimated. Cite original data sources as required and inspect workbook terms.' + (' Local workbook provenance and version are unverified.' if local_file else '')}
    finally:
        w.close()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('country')
    p.add_argument('start', type=int)
    p.add_argument('end', type=int)
    p.add_argument('--local-file')
    a = p.parse_args()
    print(json.dumps(query(a.country, a.start, a.end, a.local_file), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
