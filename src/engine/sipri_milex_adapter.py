"""SIPRI 2026 military expenditure workbook, with source notes and cell colors."""
import release_runtime
import io
import requests
import openpyxl
URL = 'https://www.sipri.org/sites/default/files/SIPRI-Milex-data-1949-2025_v1.2.xlsx'
SHEETS = {'current_usd': ('Current US$', 'million current USD'), 'constant_usd': ('Constant (2024) US$', 'million constant 2024 USD'), 'gdp_share': ('Share of GDP', 'fraction of GDP'), 'per_capita': ('Per capita', 'current USD per person')}

def query(country, *, metric='current_usd', year_from=2024, year_to=2025):
    if metric not in SHEETS or not 1949 <= year_from <= year_to <= 2025 or year_to - year_from > 49:
        raise ValueError('invalid metric or year range (maximum 50 years)')
    with requests.get(URL, timeout=45, stream=True) as r:
        r.raise_for_status()
        content = r.raw.read(5000001, decode_content=True)
    if len(content) > 5000000:
        raise ValueError('workbook exceeds download limit')
    wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    try:
        sheet, unit = SHEETS[metric]
        ws = wb[sheet]
        rows = iter(ws)
        header = next((row for row in rows if row[0].value == 'Country'), None)
        if not header:
            raise ValueError('missing expected headers')
        columns = {cell.value: n for n, cell in enumerate(header) if type(cell.value) is int and 1949 <= cell.value <= 2025}
        match = next((row for row in rows if str(row[0].value).casefold() == country.casefold()), None)
        if match is None:
            raise ValueError('country not found; names must match source exactly')
        notes = match[1].value
        values = []
        for year in range(year_from, year_to + 1):
            if year not in columns:
                continue
            cell = match[columns[year]]
            color = cell.font.color
            color_info = None if color is None else {'type': color.type, 'value': getattr(color, color.type)}
            values.append({'year': year, 'value': cell.value, 'unit': unit, 'source_font_color': color_info, 'number_format': cell.number_format})
        footnotes = [[c.value for c in row] for row in wb['Footnotes'].iter_rows() if any((c.value is not None for c in row))]
        return {'source': 'SIPRI Military Expenditure Database', 'source_url': URL, 'sheet': sheet, 'country': match[0].value, 'country_notes': notes, 'footnotes': footnotes, 'records': values, 'terms': 'https://www.sipri.org/about/terms-and-conditions', 'note': 'Independent research estimates, not necessarily official government figures. Inspect country notes, footnotes and original cell color for uncertainty. GDP share is a fraction, not a percentage. SIPRI restricts non-commercial fair use and copying to less than 10% of the dataset; other uses require authorization.'}
    finally:
        wb.close()
