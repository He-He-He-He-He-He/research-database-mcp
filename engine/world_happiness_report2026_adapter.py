"""World Happiness Report 2026 public Figure 2.1 three-year averages."""
import release_runtime
import io
import openpyxl
import requests
URL = 'https://files.worldhappiness.report/WHR26_Data_Figure_2.1.xlsx'

def query(country, end_year_from=2012, end_year_to=2025):
    if not isinstance(country, str) or not country.strip() or len(country) > 100:
        raise ValueError('country must be source country name')
    if any((type(x) is not int for x in (end_year_from, end_year_to))) or not 2012 <= end_year_from <= end_year_to <= 2025:
        raise ValueError('ending years must be 2012..2025')
    with requests.get(URL, timeout=45, stream=True) as r:
        r.raise_for_status()
        body = r.raw.read(2000001, decode_content=True)
    if len(body) > 2000000:
        raise ValueError('workbook exceeds size limit')
    w = openpyxl.load_workbook(io.BytesIO(body), read_only=True, data_only=True)
    try:
        rows = iter(w['Data for Figure 2.1 (2011–2025)'].values)
        header = next(rows)
        required = {'Year', 'Rank', 'Country name', 'Life evaluation (3-year average)', 'Lower whisker', 'Upper whisker'}
        if not required.issubset(header):
            raise ValueError('unexpected workbook columns')
        output = []
        for row in rows:
            item = dict(zip(header, row))
            name = item['Country name']
            year = item['Year']
            if isinstance(name, str) and name.casefold() == country.strip().casefold() and (type(year) in (int, float)) and (end_year_from <= year <= end_year_to):
                output.append({'country': name, 'period_end_year': int(year), 'period_start_year': int(year) - 2, 'rank': item['Rank'], 'life_evaluation': item['Life evaluation (3-year average)'], 'lower_95_percent': item['Lower whisker'], 'upper_95_percent': item['Upper whisker']})
        return {'source': 'World Happiness Report 2026, Figure 2.1', 'source_url': URL, 'scale': 'Cantril ladder 0 to 10; three-year average', 'records': output, 'note': 'Survey-based research report, not official UN statistics; period is a three-year average, not a single-year observation. Separate redistribution permission and other Gallup data access are not established.'}
    finally:
        w.close()
