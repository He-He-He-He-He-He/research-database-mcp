"""WHO GHED 2025 bulk workbook: coded indicators, country and annual observations."""
import release_runtime
import io
import re
import tempfile
import openpyxl
import requests
URL = 'https://apps.who.int/nha/database/Home/IndicatorsDownload/en'

def _open(local_file):
    if local_file:
        return (openpyxl.load_workbook(local_file, read_only=True, data_only=True), None)
    temp = tempfile.TemporaryFile()
    try:
        with requests.get(URL, stream=True, timeout=120) as r:
            r.raise_for_status()
            total = 0
            for block in r.iter_content(1024 * 1024):
                total += len(block)
                if total > 50000000:
                    raise ValueError('workbook exceeds 50 MB limit')
                temp.write(block)
        temp.seek(0)
        return (openpyxl.load_workbook(temp, read_only=True, data_only=True), temp)
    except Exception:
        temp.close()
        raise

def indicators(keyword='', *, local_file=None, limit=30):
    if not isinstance(keyword, str) or len(keyword) > 100 or type(limit) is not int or (not 1 <= limit <= 100):
        raise ValueError('invalid keyword or limit')
    w, f = _open(local_file)
    try:
        rows = iter(w['Codebook'].values)
        headers = next(rows)
        matches = [dict(zip(headers, row)) for row in rows if keyword.casefold() in str(row[0]).casefold() + ' ' + str(row[1]).casefold()]
        return {'source': local_file if local_file else URL, 'note': 'Local workbook provenance and version are unverified.' if local_file else 'WHO workbook may be updated.', 'total_matches': len(matches), 'records': matches[:limit]}
    finally:
        w.close()
        if f:
            f.close()

def query(country_code, indicator, year_from, year_to, *, local_file=None):
    if not re.fullmatch('[A-Z]{3}', country_code) or not re.fullmatch('[A-Za-z0-9_]{1,80}', indicator):
        raise ValueError('invalid ISO3 or indicator')
    if any((type(x) is not int for x in (year_from, year_to))) or not 2000 <= year_from <= year_to <= 2024:
        raise ValueError('valid years are 2000..2024')
    w, f = _open(local_file)
    try:
        codes = iter(w['Codebook'].values)
        ch = next(codes)
        matches = [dict(zip(ch, r)) for r in codes if r[0] == indicator]
        if len(matches) != 1:
            raise ValueError('indicator not found or ambiguous')
        sheet = w['Data']
        header = next(sheet.iter_rows(min_row=1, max_row=1, values_only=True))
        if header.count(indicator) != 1 or not {'location', 'code', 'year'}.issubset(header):
            raise ValueError('unexpected WHO data columns')
        ix = header.index(indicator)
        loc = header.index('location')
        code = header.index('code')
        yr = header.index('year')
        out = []
        for row in sheet.iter_rows(min_row=2, values_only=True, max_col=max(ix, loc, code, yr) + 1):
            if row[code] == country_code and type(row[yr]) is int and (year_from <= row[yr] <= year_to):
                out.append({'country': row[loc], 'year': row[yr], 'value': row[ix]})
        v = [r[0] for r in w['Version'].iter_rows(values_only=True) if r[0] is not None]
        meta = iter(w['Metadata'].values)
        mh = next(meta)
        notes = [dict(zip(mh, r)) for r in meta if r[1] == country_code and r[4] == indicator]
        return {'source': 'Local workbook (provenance and version unverified)' if local_file else 'WHO Global Health Expenditure Database', 'source_url': local_file if local_file else URL, 'version_notes': v, 'indicator': matches[0], 'country_code': country_code, 'country_indicator_metadata': notes, 'records': out}
    finally:
        w.close()
        if f:
            f.close()
