"""World Bank WFSO April 2026 released modelled food insecurity data."""
import release_runtime
import csv, io, re, zipfile, requests
PAGE = 'https://microdata.worldbank.org/catalog/6103/get-microdata'
URL = 'https://microdata.worldbank.org/catalog/6103/download/358432'
METADATA = 'https://microdata.worldbank.org/catalog/6103'
TERMS = 'https://data.worldbank.org/summary-terms-of-use'
NOTE = 'April 2026 fixed vintage. Values mix historical model estimates, contemporary estimates and projections; retain each row type, flag, note and unit. IPC-compatible estimates are model conversions, not original IPC classifications. Data include three-year centered averages, not single-year measurements. FAO may revise historical series; different vintages are not directly comparable. Geographic country totals and global aggregates overlap. Download accepts World Bank dataset terms; attribution and restrictions on third-party materials apply.'

def query(country, start, end, keyword='', limit=100):
    if not isinstance(country, str) or not re.fullmatch('[A-Za-z]{3}', country):
        raise ValueError('country must be three letters')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start, end, limit))) or not 1999 <= start <= end <= 2030 or (not 1 <= limit <= 500):
        raise ValueError('invalid years or limit')
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('invalid keyword')
    s = requests.Session()
    a = s.get(PAGE, timeout=30)
    a.raise_for_status()
    a = s.post(PAGE, data={'accept': 'Accept'}, timeout=30)
    a.raise_for_status()
    r = s.get(URL, timeout=60)
    r.raise_for_status()
    if len(r.content) > 3000000:
        raise ValueError('compressed dataset exceeds 3 MB')
    z = zipfile.ZipFile(io.BytesIO(r.content))
    files = z.infolist()
    if len(files) != 1 or files[0].filename != 'WFSO_apr_2026.csv' or files[0].file_size > 40000000:
        raise ValueError('unexpected dataset archive')
    with z.open(files[0]) as f:
        reader = csv.DictReader(io.TextIOWrapper(f, encoding='utf-8-sig', newline=''))
        expected = {'iso3c', 'country', 'indicator_short', 'indicator_long', 'unit', 'year', 'value', 'flag', 'type', 'note', 'estimated'}
        if set(reader.fieldnames or []) != expected:
            raise ValueError('unexpected CSV columns')
        out = []
        matched = 0
        for x in reader:
            if x['iso3c'] == country.upper() and x['year'].isdigit() and (start <= int(x['year']) <= end) and (keyword.casefold() in (x['indicator_short'] + ' ' + x['indicator_long']).casefold()):
                matched += 1
                if len(out) < limit:
                    out.append(x)
    return {'source': URL, 'metadata': METADATA, 'terms': TERMS, 'vintage': 'April 2026', 'matched': matched, 'returned': len(out), 'records': out, 'note': NOTE}
