"""Tanzania NBS census mainland Table 1; census values and old projections separated."""
import release_runtime
import re
import subprocess
import fitz
URL = 'https://www.nbs.go.tz/nbs/takwimu/Census2022/Administrative_units_Population_Distribution_Report_Tanzania_Mainland_volume1b.pdf'
TITLE = 'Population by Region and Average Annual Intercensal Population Growth Rate; 2012 and'

def _parse_pdf(data):
    if len(data) > 20000000 or not data.startswith(b'%PDF'):
        raise RuntimeError('Invalid Tanzania NBS census PDF')
    with fitz.open(stream=data, filetype='pdf') as doc:
        if len(doc) != 263:
            raise RuntimeError('Unexpected Tanzania NBS PDF pagination')
        text = doc[27].get_text()
    if TITLE not in text or 'Tanzania Mainland' not in text:
        raise RuntimeError('Expected Tanzania mainland census table missing')
    lines = [s.strip() for s in text[text.index('Tanzania Mainland', text.index(TITLE)):].splitlines() if s.strip()]
    if len(lines) != 27 * 7:
        raise RuntimeError('Unexpected Tanzania census row count')
    out = []
    for i in range(27):
        name, *v = lines[i * 7:(i + 1) * 7]
        if not re.fullmatch('[A-Za-z ]+', name) or not all((re.fullmatch('\\d{1,3}(?:,\\d{3})*', x) for x in v[:4])) or (not all((re.fullmatch('\\d+\\.\\d+', x) for x in v[4:]))):
            raise RuntimeError('Unexpected Tanzania census row ' + name)
        if int(v[2].replace(',', '')) - int(v[0].replace(',', '')) != int(v[3].replace(',', '')):
            raise RuntimeError('Population difference inconsistent: ' + name)
        out.append({'region': name, 'census_2012_persons_raw': v[0], 'projection_2022_persons_raw': v[1], 'census_2022_persons_raw': v[2], 'increase_2012_2022_persons_raw': v[3], 'annual_growth_2002_2012_percent_raw': v[4], 'annual_growth_2012_2022_percent_raw': v[5]})
    if out[0]['region'] != 'Tanzania Mainland' or len({r['region'] for r in out}) != 27:
        raise RuntimeError('Missing or duplicate Tanzania mainland regions')
    if sum((int(r['census_2022_persons_raw'].replace(',', '')) for r in out[1:])) != int(out[0]['census_2022_persons_raw'].replace(',', '')):
        raise RuntimeError('Mainland regional total mismatch')
    return out

def regions():
    p = release_runtime.run(['/usr/bin/curl', '-fsSL', '--max-time', '55', '--max-filesize', '20000000', URL], capture_output=True, timeout=60)
    if p.returncode:
        raise RuntimeError('Tanzania NBS PDF request failed: ' + p.stderr.decode('utf-8', 'replace').strip())
    return {'source': 'National Bureau of Statistics, Tanzania', 'title': '2022 Population and Housing Census: Administrative Units Population Distribution Report, Tanzania Mainland', 'source_url': URL, 'table': 'Table 1: Population by Region and Average Annual Intercensal Population Growth Rate; 2012 and 2022 PHCs', 'pdf_page': 28, 'unit': 'population and increase: persons; average annual intercensal growth rates: percent', 'coverage': 'Tanzania Mainland only; Zanzibar is excluded', 'note': '2022 projections are earlier projections, separate from the 2022 census count. Annual rates cover different intercensal periods. Mainland total overlaps 26 regions; do not add together. Official report, not current population.', 'items': _parse_pdf(p.stdout)}
