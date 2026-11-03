"""UN Tourism official inbound tourism workbook snapshots, filtered locally."""
from __future__ import annotations
import release_runtime
import io
import requests
import openpyxl
DOC = 'https://www.untourism.int/tourism-statistics/tourism-data-inbound-tourism'
FILES = {'arrivals': 'https://pre-webunwto.s3.eu-west-1.amazonaws.com/s3fs-public/2026-09/UN_Tourism_inbound_arrivals_09_2026.xlsx', 'expenditure': 'https://pre-webunwto.s3.amazonaws.com/s3fs-public/2025-12/UN_Tourism_inbound_expenditure_12_2025.xlsx', 'origin': 'https://pre-webunwto.s3.amazonaws.com/s3fs-public/2025-12/UN_Tourism_inbound_arrivals_by_region_12_2025.xlsx', 'purpose': 'https://pre-webunwto.s3.amazonaws.com/s3fs-public/2025-12/UN_Tourism_inbound_arrivals_by_purpose_12_2025.xlsx', 'transport': 'https://pre-webunwto.s3.amazonaws.com/s3fs-public/2025-12/UN_Tourism_inbound_arrivals_by_transport_12_2025.xlsx', 'accommodation': 'https://pre-webunwto.s3.eu-west-1.amazonaws.com/s3fs-public/2026-07/UN_Tourism_inbound_accommodation_07_2026.xlsx'}

def data(dataset, country='', start=None, end=None, indicator='', offset=0, limit=20):
    if dataset not in FILES:
        raise ValueError('unknown dataset')
    if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:
        raise ValueError('offset must be nonnegative integer')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 1000):
        raise ValueError('limit must be between 1 and 1000')
    for v in (start, end):
        if v is not None and (not isinstance(v, int) or isinstance(v, bool) or (not 1900 <= v <= 2100)):
            raise ValueError('invalid year')
    if start is not None and end is not None and (start > end):
        raise ValueError('start must not exceed end')
    response = requests.get(FILES[dataset], timeout=90)
    response.raise_for_status()
    workbook = openpyxl.load_workbook(io.BytesIO(response.content), read_only=True, data_only=True)
    try:
        sheet = workbook['Data']
        iterator = sheet.iter_rows(values_only=True)
        headers = list(next(iterator))
        needed = {'reporter_area_label', 'year', 'indicator_code', 'value', 'unit', 'flag', 'notes'}
        if not needed.issubset(headers) or len(headers) != len(set(headers)):
            raise ValueError('unexpected workbook headers')
        rows = []
        for values in iterator:
            row = dict(zip(headers, values))
            if country and str(row['reporter_area_label']).casefold() != country.strip().casefold():
                continue
            if indicator and str(row['indicator_code']).casefold() != indicator.strip().casefold():
                continue
            year = row['year']
            if (start is not None or end is not None) and (not isinstance(year, (int, float))):
                continue
            if start is not None and year < start:
                continue
            if end is not None and year > end:
                continue
            rows.append(row)
        overview = []
        if 'Overview' in workbook:
            for values in workbook['Overview'].iter_rows(values_only=True):
                overview.extend((v for v in values if isinstance(v, str) and v.strip()))
        return {'source': FILES[dataset], 'catalog': DOC, 'dataset': dataset, 'download_bytes': len(response.content), 'fields': headers, 'overview': overview, 'total_rows': len(rows), 'offset': offset, 'limit': limit, 'rows': rows[offset:offset + limit], 'notes': ['Official workbook snapshot, locally filtered; dates differ by dataset and newer publications may exist.', 'Retain indicator, origin/partner, unit, flags and notes: arrivals or trips are not unique individuals; tourists and visitors differ.', 'Data collection and processing are transitional according to workbook overview; missing records are not zero.']}
    finally:
        workbook.close()
