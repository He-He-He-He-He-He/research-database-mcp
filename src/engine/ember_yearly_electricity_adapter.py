"""Ember annual electricity generation and capacity per country/source."""
import release_runtime
import csv
import io
import re
import requests
URL = 'https://files.ember-energy.org/public-downloads/generation/outputs/release_generation_yearly_global.csv'

def query(country_code, year_from, year_to, *, electricity_source=None, limit=100, offset=0):
    if not re.fullmatch('[A-Z]{3}', country_code):
        raise ValueError('country_code must be uppercase ISO3')
    if any((type(x) is not int for x in (year_from, year_to, limit))) or not 1900 <= year_from <= year_to <= 2100 or (not 1 <= limit <= 100) or (type(offset) is not int) or (offset < 0):
        raise ValueError('invalid year range or limit')
    if electricity_source is not None and (not isinstance(electricity_source, str) or len(electricity_source) > 80):
        raise ValueError('invalid source name')
    with requests.get(URL, stream=True, timeout=90) as response:
        response.raise_for_status()
        content = response.raw.read(30000001, decode_content=True)
    if len(content) > 30000000:
        raise ValueError('CSV exceeds size limit')
    rows = csv.DictReader(io.StringIO(content.decode('utf-8-sig')))
    needed = {'ISO 3 code', 'Year', 'Electricity source', 'Is aggregated source', 'Generation (TWh)', 'Capacity (GW)'}
    if not needed.issubset(rows.fieldnames or []):
        raise ValueError('unexpected source CSV columns')
    output = []
    for row in rows:
        if row['ISO 3 code'] != country_code or not row['Year'].isdigit() or (not year_from <= int(row['Year']) <= year_to):
            continue
        if electricity_source is not None and row['Electricity source'].casefold() != electricity_source.casefold():
            continue

        def number(key):
            value = row.get(key, '')
            return None if not value else float(value)
        output.append({'area': row['Area'], 'iso3': row['ISO 3 code'], 'year': int(row['Year']), 'electricity_source': row['Electricity source'], 'is_aggregated_source': row['Is aggregated source'], 'generation_twh': number('Generation (TWh)'), 'share_of_generation_percent': number('Share of generation (%)'), 'capacity_gw': number('Capacity (GW)'), 'raw_values': {k: row.get(k, '') for k in ('Generation (TWh)', 'Share of generation (%)', 'Capacity (GW)')}})
    return {'source': 'Ember Yearly Electricity Data', 'source_url': URL, 'license': 'CC BY 4.0', 'total_matches': len(output), 'offset': offset, 'returned': len(output[offset:offset + limit]), 'next_offset': offset + limit if offset + limit < len(output) else None, 'truncated': offset + limit < len(output), 'records': output[offset:offset + limit], 'note': 'Independent Ember compilation from multiple sources, not a single official national dataset. Aggregated categories overlap their components; generation and capacity are different measures. Missing is not zero. Data may be revised; attribution required. Each request refetches the source file, which may change and reorder records; raw_values preserve source numeric strings.'}
