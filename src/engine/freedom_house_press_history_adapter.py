"""Freedom House historical Freedom of the Press, 2002–2017 editions."""
import release_runtime
import io
import openpyxl
import requests
URL = 'https://freedomhouse.org/sites/default/files/2020-02/FOTP1980-FOTP2017_Public-Data.xlsx'

def query(country, edition_from=2002, edition_to=2017):
    if not isinstance(country, str) or not country.strip() or len(country) > 100:
        raise ValueError('country must be the source country name')
    if any((type(x) is not int for x in (edition_from, edition_to))) or not 2002 <= edition_from <= edition_to <= 2017:
        raise ValueError('editions must be between 2002 and 2017')
    with requests.get(URL, timeout=30, stream=True) as r:
        r.raise_for_status()
        content = r.raw.read(2000001, decode_content=True)
    if len(content) > 2000000:
        raise ValueError('source workbook exceeds size limit')
    w = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    try:
        s = w['Data']
        editions = next(s.iter_rows(min_row=3, max_row=3, values_only=True))
        covered = next(s.iter_rows(min_row=4, max_row=4, values_only=True))
        heads = next(s.iter_rows(min_row=5, max_row=5, values_only=True))
        match = [r for r in s.iter_rows(min_row=6, max_row=215, values_only=True) if isinstance(r[0], str) and r[0].casefold() == country.strip().casefold()]
        if len(match) != 1:
            raise ValueError('country not found or ambiguous')
        row = match[0]
        result = []
        for i, ed in enumerate(editions):
            if type(ed) is int and edition_from <= ed <= edition_to:
                names = heads[i:i + 5]
                if names != ('A-Legal', 'B-Political', 'C-Economic', 'Total Score', 'Status'):
                    raise ValueError('unexpected historical dataset columns')
                result.append({'edition': ed, 'year_covered': covered[i], 'scores': dict(zip(names, row[i:i + 5]))})
        return {'source': 'Freedom House Freedom of the Press', 'source_url': URL, 'country': row[0], 'score_direction': 'higher means less press freedom', 'records': result, 'note': 'Historical independent organization assessment, not government statistics; edition generally covers the previous year. Separate from RSF methodology. Redistribution and commercial-use permission have not been established.'}
    finally:
        w.close()
