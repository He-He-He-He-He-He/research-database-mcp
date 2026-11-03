"""Penn World Table 11.0 country-year estimates, 1950–2023."""
import release_runtime
import io
import re
import openpyxl
import requests
URL = 'https://dataverse.nl/api/access/datafile/554105'

def _workbook(local_file):
    if local_file:
        return openpyxl.load_workbook(local_file, read_only=True, data_only=True)
    with requests.get(URL, stream=True, timeout=90) as r:
        r.raise_for_status()
        body = r.raw.read(10000001, decode_content=True)
    if len(body) > 10000000:
        raise ValueError('workbook exceeds size limit')
    return openpyxl.load_workbook(io.BytesIO(body), read_only=True, data_only=True)

def indicators(*, local_file=None):
    wb = _workbook(local_file)
    try:
        rows = iter(wb['Legend'].values)
        next(rows)
        return [{'code': r[0], 'definition': r[1]} for r in rows if r[0] and r[1]]
    finally:
        wb.close()

def query(country_code, indicator, year_from=1950, year_to=2023, *, local_file=None):
    if not re.fullmatch('[A-Z]{3}', country_code) or not re.fullmatch('[A-Za-z0-9_]{1,40}', indicator):
        raise ValueError('invalid country code or indicator')
    if any((type(x) is not int for x in (year_from, year_to))) or not 1950 <= year_from <= year_to <= 2023:
        raise ValueError('years must be 1950..2023')
    wb = _workbook(local_file)
    try:
        defs = [r for r in wb['Legend'].values if r[0] == indicator]
        if len(defs) != 1:
            raise ValueError('indicator not found or ambiguous')
        rows = iter(wb['Data'].values)
        headers = next(rows)
        if indicator not in headers or not {'countrycode', 'country', 'year'}.issubset(headers):
            raise ValueError('unexpected data columns')
        country_ix, name_ix, year_ix, value_ix = (headers.index(x) for x in ('countrycode', 'country', 'year', indicator))
        out = []
        for row in rows:
            if row[country_ix] == country_code and type(row[year_ix]) is int and (year_from <= row[year_ix] <= year_to):
                out.append({'country': row[name_ix], 'year': row[year_ix], 'value': row[value_ix]})
        return {'source': 'Local workbook (provenance and version unverified)' if local_file else 'Penn World Table 11.0, Groningen Growth and Development Centre', 'source_url': local_file if local_file else URL, 'license': None if local_file else 'CC BY 4.0', 'indicator': indicator, 'definition': defs[0][1], 'country_code': country_code, 'records': out}
    finally:
        wb.close()
