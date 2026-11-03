"""OECD current well-being dashboard indicators and source observations."""
import release_runtime
import csv, io, re, xml.etree.ElementTree as ET, requests
BASE = 'https://sdmx.oecd.org/public/rest/'
FLOW = 'OECD.WISE.WDP,DSD_HSL@DF_HSL_CWB,1.1'
STRUCT = BASE + 'dataflow/OECD.WISE.WDP/DSD_HSL@DF_HSL_CWB/1.1?references=all'
DOC = 'https://www.oecd.org/en/data/tools/well-being-data-monitor.html'
NOTE = 'OECD well-being indicators have different units, population bases, survey years, methodologies and underlying providers. Values are not a single composite happiness score. Repeated annual values may reflect underlying survey-period treatment; inspect official definitions and source before describing year-on-year change. Keep unit, multiplier, year, statuses, and missing values. Some underlying series may have third-party reuse terms.'

def catalog(keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('invalid keyword')
    r = requests.get(STRUCT, timeout=60)
    r.raise_for_status()
    if len(r.content) > 10000000:
        raise ValueError('structure too large')
    root = ET.fromstring(r.content)
    ns = {'s': 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure', 'c': 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common'}
    cs = root.findall('.//s:Codelist[@id="CL_MEASURE"][@agencyID="OECD.WISE.WDP"]', ns)
    if len(cs) != 1:
        raise ValueError('unexpected measure codelist')
    rows = []
    for x in cs[0].findall('s:Code', ns):
        name = next((n.text for n in x.findall('c:Name', ns) if n.get('{http://www.w3.org/XML/1998/namespace}lang') == 'en'), '')
        if keyword.casefold() in (x.get('id', '') + ' ' + name).casefold():
            rows.append({'id': x.get('id'), 'name': name})
    return {'source': STRUCT, 'records': rows, 'note': NOTE}

def query(country, indicator, start, end):
    if not isinstance(country, str) or not re.fullmatch('[A-Za-z]{3}', country):
        raise ValueError('country must be three letters')
    if not isinstance(indicator, str) or not re.fullmatch('[A-Z0-9_]{1,30}', indicator):
        raise ValueError('invalid indicator code')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start, end))) or not 1900 <= start <= end <= 2100:
        raise ValueError('invalid years')
    country = country.upper()
    r = requests.get(BASE + 'data/' + FLOW + f'/{country}.{indicator}.._T._T._T.', params={'startPeriod': start, 'endPeriod': end, 'format': 'csvfile'}, timeout=40)
    if r.status_code == 204 or (r.status_code == 404 and r.text.strip() in ('NoRecordsFound', 'NoResultsFound')):
        rows = []
    else:
        r.raise_for_status()
        reader = csv.DictReader(io.StringIO(r.text))
        needed = {'REF_AREA', 'MEASURE', 'UNIT_MEASURE', 'AGE', 'SEX', 'EDUCATION_LEV', 'TIME_PERIOD', 'OBS_VALUE', 'OBS_STATUS', 'UNIT_MULT'}
        if not reader.fieldnames or not needed.issubset(reader.fieldnames):
            raise ValueError('unexpected OECD CSV')
        rows = list(reader)
        dims = {'REF_AREA': country, 'MEASURE': indicator, 'AGE': '_T', 'SEX': '_T', 'EDUCATION_LEV': '_T'}
        if any((any((x.get(k) != v for k, v in dims.items())) for x in rows)):
            raise ValueError('unexpected OECD dimensions')
    return {'source': r.url, 'documentation': DOC, 'structure': STRUCT, 'country': country, 'indicator': indicator, 'records': rows, 'note': NOTE}
