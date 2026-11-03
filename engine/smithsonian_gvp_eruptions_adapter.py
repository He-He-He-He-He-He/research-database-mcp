"""Smithsonian GVP confirmed eruption list downloaded 24 April 2026."""
import release_runtime
import io
import openpyxl
import requests
URL = 'https://volcano.si.edu/database/GVP_Eruption_List_Holocene_20260424.xlsx'

def query(volcano_name, year_from, year_to, limit=100):
    if not isinstance(volcano_name, str) or not volcano_name.strip() or len(volcano_name) > 100:
        raise ValueError('volcano name required')
    if any((type(x) is not int for x in (year_from, year_to, limit))) or not -10000 <= year_from <= year_to <= 2026 or (not 1 <= limit <= 100):
        raise ValueError('invalid year range or limit')
    with requests.get(URL, stream=True, timeout=45) as r:
        r.raise_for_status()
        content = r.raw.read(5000001, decode_content=True)
    if len(content) > 5000000:
        raise ValueError('workbook exceeds limit')
    wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    try:
        sheet = wb['Eruption List']
        metadata = next(sheet.iter_rows(min_row=1, max_row=1, values_only=True))
        headers = next(sheet.iter_rows(min_row=2, max_row=2, values_only=True))
        if not {'Volcano Name', 'Start Year', 'Eruption Number'}.issubset(headers):
            raise ValueError('unexpected workbook structure')
        found = []
        for row in sheet.iter_rows(min_row=3, values_only=True):
            item = dict(zip(headers, row))
            year = item['Start Year']
            if isinstance(item['Volcano Name'], str) and item['Volcano Name'].casefold() == volcano_name.strip().casefold() and (type(year) is int) and (year_from <= year <= year_to):
                found.append(item)
        return {'source': 'Smithsonian Global Volcanism Program', 'source_url': URL, 'workbook_metadata': list(metadata), 'year_filter': 'eruption start year', 'total_matches': len(found), 'records': found[:limit], 'note': 'Static workbook carries version 5.3.5 while its Info sheet and website reference different versions; not necessarily latest. This sheet has no country field. Preserve date uncertainty and VEI annotations; filter is by eruption start year.'}
    finally:
        wb.close()
