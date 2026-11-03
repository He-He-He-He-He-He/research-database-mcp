"""RSF World Press Freedom Index public annual CSVs, 2022–2026."""
import release_runtime
import csv
import io
import re
import requests
BASE = 'https://rsf.org/sites/default/files/import_classement/'

def query(country_code, year_from=2022, year_to=2026):
    if not re.fullmatch('[A-Z]{3}', country_code) or not 2022 <= year_from <= year_to <= 2026:
        raise ValueError('country must be a three-letter source code; years 2022..2026')
    results = []
    for year in range(year_from, year_to + 1):
        url = f'{BASE}{year}.csv'
        with requests.get(url, stream=True, timeout=30) as response:
            response.raise_for_status()
            data = response.raw.read(1000001, decode_content=True)
        if len(data) > 1000000:
            raise ValueError('annual CSV exceeds size limit')
        try:
            text = data.decode('utf-8-sig')
        except UnicodeDecodeError:
            text = data.decode('cp1252')
        rows = list(csv.DictReader(io.StringIO(text), delimiter=';'))
        hits = [row for row in rows if row.get('ISO') == country_code]
        if len(hits) > 1:
            raise ValueError('duplicate source country')
        if not hits:
            results.append({'edition_year': year, 'source_url': url, 'available': False})
            continue
        row = hits[0]
        if row.get('Year (N)') != str(year):
            raise ValueError('source edition year mismatch')
        value = row.get('Score ' + str(year), row.get('Score'))
        try:
            score = float(value.replace(',', '.'))
            rank = int(row['Rank'])
        except (ValueError, TypeError, AttributeError):
            raise ValueError('unexpected score/rank')
        fields = ['Political Context', 'Economic Context', 'Legal Context', 'Social Context', 'Safety']
        dimensions = {}
        for name in fields:
            raw = row.get(name, '')
            dimensions[name] = float(raw.replace(',', '.')) if raw else None
        results.append({'edition_year': year, 'source_url': url, 'available': True, 'country_name': row.get('Country_EN'), 'country_code': country_code, 'score': score, 'rank': rank, 'dimensions': dimensions, 'source_row': row})
    return {'source': 'Reporters Without Borders World Press Freedom Index', 'methodology': 'https://rsf.org/en/methodology-used-compiling-world-press-freedom-index-2025', 'records': results, 'note': 'Independent advocacy organization assessment, not official government statistics. Edition commonly reflects the preceding calendar year; cross-year comparability requires reviewing methodology. source_row preserves original strings and decimal separators. Redistribution and commercial-use permission have not been established.'}
