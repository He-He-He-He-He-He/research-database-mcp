"""International IDEA's public election turnout workbook export."""
import release_runtime
import io
import re
import openpyxl
import requests
URL = 'https://www.idea.int/data-tools/export?type=region_only&themeId=293&world=all&loc=home'

def query(country_code, year_from=1945, year_to=2100, election_type=None, limit=100):
    if not re.fullmatch('[A-Z]{3}', country_code):
        raise ValueError('country_code must be ISO3')
    if any((type(x) is not int for x in (year_from, year_to, limit))) or not 1945 <= year_from <= year_to <= 2100 or (not 1 <= limit <= 100):
        raise ValueError('invalid years or limit')
    if election_type not in (None, 'Parliamentary', 'Presidential', 'EU Parliament'):
        raise ValueError('unsupported election type')
    with requests.get(URL, timeout=60, stream=True) as response:
        response.raise_for_status()
        content = response.raw.read(5000001, decode_content=True)
    if len(content) > 5000000:
        raise ValueError('workbook exceeds size limit')
    wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    try:
        rows = iter(wb['All'].values)
        headers = next(rows)
        if not {'ISO3', 'Election Type', 'Year', 'Voter Turnout', 'VAP Turnout'}.issubset(headers):
            raise ValueError('unexpected columns')
        out = []
        for row in rows:
            item = dict(zip(headers, row))
            date = item['Year']
            if item['ISO3'] != country_code or not isinstance(date, str) or (not re.match('^\\d{4}-\\d{2}-\\d{2}$', date)):
                continue
            if not year_from <= int(date[:4]) <= year_to or (election_type and item['Election Type'] != election_type):
                continue
            out.append(item)
        return {'source': 'International IDEA Voter Turnout Database', 'source_url': URL, 'total_matches': len(out), 'limit': limit, 'truncated': len(out) > limit, 'records': out[:limit], 'note': 'When truncated increase limit up to 100 or narrow the year range. Voter turnout among registered voters and voting-age population turnout have different denominators; multiple rounds are separate elections. Source coverage and population estimates vary; redistribution permission has not been verified.'}
    finally:
        wb.close()
