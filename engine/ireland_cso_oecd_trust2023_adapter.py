"""Irish CSO published cross-country OECD Trust Survey 2023 tables."""
import release_runtime
import csv, io, re, requests
BASE = 'https://ws.cso.ie/public/api.restful/PxStat.Data.Cube_API.ReadDataset/'
DOC = 'https://www.cso.ie/en/releasesandpublications/ep/p-trsic/trustsurveyinternationalcomparisons2023/data/'
TABLES = {'trust': 'TRA210', 'services': 'TRA211'}

def query(country, table, keyword=''):
    if not isinstance(country, str) or not re.fullmatch('[A-Za-z]{2}', country):
        raise ValueError('country must be a source two-letter code')
    if table not in TABLES or not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('invalid query')
    country = country.upper()
    u = BASE + TABLES[table] + '/CSV/1.0/en'
    r = requests.get(u, timeout=40)
    r.raise_for_status()
    if len(r.content) > 5000000:
        raise ValueError('response exceeds 5 MB')
    reader = csv.DictReader(io.StringIO(r.content.decode('utf-8-sig'), newline=''))
    needed = {'STATISTIC', 'Statistic Label', 'Year', 'C03846V04596', 'OECD Countries', 'UNIT', 'VALUE'}
    if not reader.fieldnames or not needed.issubset(reader.fieldnames):
        raise ValueError('unexpected CSO CSV')
    key = 'Trust in people and institutions' if table == 'trust' else 'Public Service'
    if key not in reader.fieldnames:
        raise ValueError('unexpected CSO topic dimension')
    rows = [x for x in reader if x['C03846V04596'] == country and keyword.casefold() in x[key].casefold()]
    if any((x['UNIT'] != '%' or x['Year'] != '2023' for x in rows)):
        raise ValueError('unexpected unit or year')
    return {'source': u, 'documentation': DOC, 'table': TABLES[table], 'country_code': country, 'records': rows, 'note': 'Irish CSO republication of OECD Trust Survey 2023, not a new OECD data collection. Survey response shares, not objective performance or universal public opinion. Trust categories are distinct 0–4, 5, 6–10 and do-not-know responses; retain source labels and denominators. Service satisfaction is for respondents with recent service contact, not all residents. Source may use Irish-specific examples in common question labels; consult country questionnaire and methodology before comparison. Keep missing and suppressed cells unchanged.'}
