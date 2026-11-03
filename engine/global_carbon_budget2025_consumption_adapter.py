"""Global Carbon Budget 2025 national consumption-based fossil carbon estimates."""
import release_runtime
import io
import openpyxl
import requests
URL = 'https://globalcarbonbudget.org/download/2345/?tmstv=1762815968'

def query(country, year_from, year_to, *, local_file=None):
    if not isinstance(country, str) or not country.strip() or len(country) > 100:
        raise ValueError('country must be a source country name')
    if any((type(x) is not int for x in (year_from, year_to))) or not 1990 <= year_from <= year_to <= 2023:
        raise ValueError('year range must be within 1990..2023')
    if local_file:
        workbook = openpyxl.load_workbook(local_file, read_only=True, data_only=True)
    else:
        with requests.get(URL, stream=True, timeout=45) as r:
            r.raise_for_status()
            data = r.raw.read(5000001, decode_content=True)
        if len(data) > 5000000:
            raise ValueError('workbook exceeds size limit')
        workbook = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    try:
        sheet = workbook['Consumption Emissions']
        header = next(sheet.iter_rows(min_row=9, max_row=9, values_only=True))
        matching = [i for i, name in enumerate(header) if isinstance(name, str) and name.casefold() == country.strip().casefold()]
        if len(matching) != 1:
            raise ValueError('source country name not found or ambiguous')
        col = matching[0]
        results = []
        for row in sheet.iter_rows(min_row=10, max_row=43, values_only=True):
            if isinstance(row[0], int) and year_from <= row[0] <= year_to:
                results.append({'year': row[0], 'value': row[col]})
        return {'source': 'Local workbook (provenance and version unverified)' if local_file else 'Global Carbon Project, National Carbon Emissions 2025 v1.0', 'url': local_file if local_file else URL, 'doi': None if local_file else 'https://doi.org/10.18160/gcp-2025', 'country': header[col], 'unit': 'million tonnes carbon per year (MtC/year)', 'measure': 'consumption-based fossil carbon emissions', 'records': results, 'note': 'Research estimate incorporating emissions embodied in trade; do not sum with territorial emissions. Carbon mass, not CO2 mass: workbook uses 1 MtC = 3.664 MtCO2. Cite the original sources; redistribution rights should be checked.' + (' Local workbook provenance and version are unverified.' if local_file else '')}
    finally:
        workbook.close()
