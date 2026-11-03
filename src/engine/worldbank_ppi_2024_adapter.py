"""World Bank PPI 2024 STATA panel: read official snapshot, filter locally."""
from __future__ import annotations
import release_runtime
import io
import math
import requests
import pandas as pd
URL = 'https://www.worldbank.org/content/dam/PPI/documents/2024-PPI-Full-DTA.dta'
DOCUMENTATION = 'https://ppi.worldbank.org/en/ppidata'
METHODOLOGY = 'https://ppi.worldbank.org/en/methodology/faq'

def query(country=None, start=None, end=None, sector=None, page=1, size=20):
    if not isinstance(page, int) or isinstance(page, bool) or page < 1:
        raise ValueError('page must be a positive integer')
    if not isinstance(size, int) or isinstance(size, bool) or (not 1 <= size <= 100):
        raise ValueError('size must be 1–100')
    for year in (start, end):
        if year is not None and (not isinstance(year, int) or isinstance(year, bool) or (not 1900 <= year <= 2100)):
            raise ValueError('years must be integers from 1900 to 2100')
    if start is not None and end is not None and (start > end):
        raise ValueError('start cannot exceed end')
    response = requests.get(URL, timeout=90)
    response.raise_for_status()
    reader = pd.io.stata.StataReader(io.BytesIO(response.content), convert_categoricals=False, convert_missing=True)
    labels = reader.variable_labels()
    timestamp = reader.time_stamp
    data = reader.read()
    mappings = reader.value_labels()
    if country:
        codes = [k for k, v in mappings['country'].items() if v.casefold() == country.strip().casefold()]
        data = data[data['country'].isin(codes)]
    if sector:
        codes = [k for k, v in mappings['sector'].items() if v.casefold() == sector.strip().casefold()]
        data = data[data['sector'].isin(codes)]
    if start is not None:
        data = data[pd.to_numeric(data['IY'], errors='coerce') >= start]
    if end is not None:
        data = data[pd.to_numeric(data['IY'], errors='coerce') <= end]
    total = len(data)
    rows = data.iloc[(page - 1) * size:page * size].to_dict(orient='records')

    def clean(v):
        if isinstance(v, pd.io.stata.StataMissingValue):
            return str(v)
        if v is None or (isinstance(v, float) and (not math.isfinite(v))):
            return None
        return v.item() if hasattr(v, 'item') else v
    rows = [{key: clean(value) for key, value in row.items()} for row in rows]
    return {'source': URL, 'documentation': DOCUMENTATION, 'methodology': METHODOLOGY, 'file_size_bytes': len(response.content), 'stata_timestamp': timestamp, 'vintage': '2024 PPI panel; publisher page describes 1990–2024', 'notes': ['Filter years refer to IY (Investment Year), not Financial Closure Year (FCY).', 'Each row is a panel observation; projects can occur across multiple years. Do not count rows as unique projects or sum stocks without inspecting their definitions.', 'Investment is total project commitment, including public and private shares, not private contribution alone. Current USDm means million current US dollars.', 'Stata missing markers are preserved as strings; value_labels maps categorical codes to their names; source-specific field labels describe units. Country and sector filters are exact case-insensitive matches.', 'This is a fixed official STATA download, not a live project API; file freshness must be checked.'], 'fields': labels, 'value_labels': {name: {str(k): v for k, v in mapping.items()} for name, mapping in mappings.items()}, 'total_rows': total, 'page': page, 'page_size': size, 'rows': rows}
