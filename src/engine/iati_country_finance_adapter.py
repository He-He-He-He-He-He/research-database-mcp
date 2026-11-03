"""IATI Country Development Finance Data: official per-country workbook reader."""
import release_runtime
import json
import tempfile
import requests
import warnings
BASE = 'https://data.countrydata.iatistandard.org/output/web/xlsx/en/'
MAX_BYTES = 100 * 1024 * 1024

def _open(url):
    response = requests.get(url, headers={'User-Agent': 'ResearchToolkit/1.0'}, timeout=90, stream=True)
    response.raise_for_status()
    return response

def countries():
    with _open(BASE + 'index.json') as r:
        payload = r.raw.read(2000001, decode_content=True)
    if len(payload) > 2000000:
        raise ValueError('Country index exceeds size limit')
    return json.loads(payload)

def query(country, year, *, transaction_type=None, limit=20, max_rows=10000):
    """Return up to limit matched workbook rows; scan is bounded and may be incomplete."""
    if not isinstance(year, int) or not 1900 <= year <= 2100:
        raise ValueError('year must be an integer in 1900..2100')
    if not 1 <= limit <= 100 or not 1 <= max_rows <= 100000:
        raise ValueError('limit must be 1..100, max_rows 1..100000')
    index = countries()
    matches = [x for x in index['countries'] if x['country_code'].upper() == country.upper()]
    if len(matches) != 1:
        raise ValueError('country or region code not in official index')
    entry = matches[0]
    filename = entry['filename']
    if filename != entry['country_code'] + '.xlsx' or not filename.replace('.xlsx', '').isalnum():
        raise ValueError('unexpected workbook filename')
    import openpyxl
    with tempfile.TemporaryFile() as f:
        with _open(BASE + filename) as r:
            size = 0
            while True:
                chunk = r.raw.read(1024 * 1024, decode_content=True)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_BYTES:
                    raise ValueError('workbook exceeds 100 MiB download limit')
                f.write(chunk)
        f.seek(0)
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', message='Workbook contains no stylesheet.*')
            wb = openpyxl.load_workbook(f, read_only=True, data_only=True)
        try:
            rows = iter(wb['Data'].values)
            headers = next(rows)
            indexes = {v: i for i, v in enumerate(headers)}
            if not all((x in indexes for x in ('Calendar Year', 'Transaction Type', 'Value (USD)'))):
                raise ValueError('unexpected workbook columns')
            out, scanned = ([], 0)
            exhausted = True
            for row in rows:
                scanned += 1
                if row[indexes['Calendar Year']] == year and (transaction_type is None or str(row[indexes['Transaction Type']]).startswith(str(transaction_type) + ' - ')):
                    out.append(dict(zip(headers, row)))
                    if len(out) >= limit:
                        exhausted = False
                        break
                if scanned >= max_rows:
                    exhausted = False
                    break
            return {'source': 'IATI Country Development Finance Data', 'source_url': BASE + filename, 'index_last_updated': index['lastUpdated'], 'country': entry, 'year': year, 'transaction_type': transaction_type, 'rows_scanned': scanned, 'complete_scan': exhausted, 'records': out, 'note': 'IATI voluntary reporting is not complete ODA; incoming funds, disbursements and expenditure are different stages and must not be blindly summed. Related project reports may overlap. A false complete_scan means additional matches may exist; large workbooks can require significant time and memory.'}
        finally:
            wb.close()
