"""Bolivia 2024 census preliminary and later published results."""
import release_runtime
import hashlib
import re
import requests
from bs4 import BeautifulSoup
PRE = 'https://cpv2024.ine.gob.bo/index.php/somos-11-312-620-bolivianos-y-santa-cruz-es-el-departamento-que-mas-crecio-y-mas-poblado/'
FINAL = 'https://cpv2024.ine.gob.bo/'
NOTES = ['The 2024-08-29 initial population count and the 2025-08-28 census results are distinct releases; the latter was not available by June 2025.', 'Both describe the census of 23 March 2024, not current estimated population. Each release retains its own geographic values and source.', 'The official map explicitly states its territorial boundaries are referential and geostatistical; this dataset does not adjudicate administrative boundaries.', 'Source figures may change; historical analysis should cite the release date and vintage, not silently substitute later results.']

def query(vintage, keyword=''):
    if vintage not in ('2024-08', '2025-08') or not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('Invalid release or keyword')
    url = PRE if vintage == '2024-08' else FINAL
    r = requests.get(url, timeout=45)
    r.raise_for_status()
    rows = []
    if vintage == '2024-08':
        soup = BeautifulSoup(r.text, 'html.parser')
        text = ' '.join(soup.get_text(' ', strip=True).split())
        for name in ('Chuquisaca', 'La Paz', 'Cochabamba', 'Oruro', 'Potosí', 'Tarija', 'Santa Cruz', 'Beni', 'Pando'):
            pattern = 'Santa Cruz es el departamento más poblado con\\s+([0-9.]+)' if name == 'Santa Cruz' else re.escape(name) + '\\s+con\\s+([0-9.]+)'
            matches = re.findall(pattern, text, re.I)
            if len(matches) != 1:
                raise ValueError('Preliminary release missing or ambiguous department')
            rows.append({'department': name, 'population': int(matches[0].replace('.', '')), 'source_fragment': re.search(pattern, text, re.I).group(0)})
        expected = 11312620
        date = '2024-08-29'
    else:
        text = r.text
        match = re.search('const\\s+departamentos\\s*=\\s*\\[(.*?)\\];', text, re.S)
        if not match:
            raise ValueError('Final department dataset missing')
        p = re.compile('\\{\\s*cod:\\s*"(\\d+)",\\s*deptoName:\\s*"([^"]+)",\\s*population:\\s*"([\\d.]+)",\\s*hombres:\\s*"([\\d.]+)",\\s*mujeres:\\s*"([\\d.]+)"\\s*,?\\s*\\}', re.S)
        for m in p.finditer(match[1]):
            vals = [int(v.replace('.', '')) for v in m.groups()[2:]]
            if vals[0] != vals[1] + vals[2]:
                raise ValueError('Final department sex total mismatch')
            rows.append({'department_code': m[1], 'department': m[2], 'population': vals[0], 'men': vals[1], 'women': vals[2], 'source_fragment': m[0]})
        expected = 11365333
        date = '2025-08-28'
    if len(rows) != 9 or len({x['department'] for x in rows}) != 9 or sum((x['population'] for x in rows)) != expected:
        raise ValueError('INE release incomplete or national cross-check failed')
    return {'source': url, 'release': vintage, 'release_date': date, 'release_date_source': PRE if vintage == '2024-08' else 'https://cpv2024.ine.gob.bo/index.php/ine-presenta-resultados-del-censo-2024-que-muestran-la-transformacion-demografica-y-avances-sociales-en-bolivia/', 'census_date': '2024-03-23', 'unit': 'persons', 'national_total': expected, 'sha256': hashlib.sha256(r.content).hexdigest(), 'notes': NOTES, 'records': [x for x in rows if keyword.casefold() in x['department'].casefold()]}
