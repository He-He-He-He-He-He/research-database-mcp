"""Malawi NSO 2018 and 2008 census by district, UNFPA-hosted main report."""
import release_runtime
import re
import subprocess
import fitz
URL = 'https://malawi.unfpa.org/sites/default/files/resource-pdf/2018%20Malawi%20Population%20and%20Housing%20Census%20Main%20Report%20%281%29.pdf'
PAGE = 'https://malawi.unfpa.org/en/publications/malawi-2018-population-and-housing-census-main-report'

def _parse_pdf(data):
    if len(data) > 15000000 or not data.startswith(b'%PDF'):
        raise RuntimeError('Invalid Malawi census PDF')
    with fitz.open(stream=data, filetype='pdf') as doc:
        if len(doc) != 311:
            raise RuntimeError('Unexpected Malawi census PDF length')
        text = doc[57].get_text()
    if 'Table A1:' not in text or 'Population of Malawi by Sex at National, Regional and District Levels' not in text or '2008 and 2018' not in text or ('\nMalawi\n' not in text):
        raise RuntimeError('Expected Malawi census table not found')
    lines = [x.strip() for x in text[text.index('\nMalawi\n') + 1:].splitlines() if x.strip()]
    if not lines[-1].startswith('Series A:') or len(lines) != 253:
        raise RuntimeError('Unexpected Malawi census table layout')
    out = []
    region = None
    for i in range(36):
        name, *v = lines[i * 7:(i + 1) * 7]
        if not re.fullmatch('[A-Za-z ]+', name) or not all((re.fullmatch('\\d{1,3}(?:,\\d{3})*', s) for s in v)):
            raise RuntimeError('Invalid Malawi census row')
        for j in (0, 3):
            if int(v[j + 1].replace(',', '')) + int(v[j + 2].replace(',', '')) != int(v[j].replace(',', '')):
                raise RuntimeError('Sex totals inconsistent for ' + name)
        if name in ('Northern', 'Central', 'Southern'):
            region = name
        level = 'country' if name == 'Malawi' else 'region' if name in ('Northern', 'Central', 'Southern') else 'district_or_city'
        if level == 'district_or_city' and region is None:
            raise RuntimeError('Missing Malawi region')
        out.append({'geography': name, 'region': region if level == 'district_or_city' else None, 'level': level, 'population_2018_raw': v[0], 'male_2018_raw': v[1], 'female_2018_raw': v[2], 'population_2008_raw': v[3], 'male_2008_raw': v[4], 'female_2008_raw': v[5]})
    if out[0]['geography'] != 'Malawi' or len([r for r in out if r['level'] == 'region']) != 3 or len({r['geography'] for r in out}) != 36:
        raise RuntimeError('Missing census geography')
    if sum((int(r['population_2018_raw'].replace(',', '')) for r in out if r['level'] == 'region')) != int(out[0]['population_2018_raw'].replace(',', '')):
        raise RuntimeError('Region total mismatch')
    return out

def districts():
    p = release_runtime.run(['/usr/bin/curl', '-fsSL', '--max-time', '45', '--max-filesize', '15000000', URL], capture_output=True, timeout=50)
    if p.returncode:
        raise RuntimeError('UNFPA-hosted Malawi census PDF request failed: ' + p.stderr.decode('utf-8', 'replace').strip())
    return {'source': 'Malawi National Statistical Office; PDF hosted by UNFPA Malawi', 'publication_page': PAGE, 'source_url': URL, 'table': 'Table A1: Population of Malawi by Sex at National, Regional and District Levels, 2008 and 2018', 'pdf_page': 58, 'reference_years': [2008, 2018], 'unit': 'persons', 'note': 'Official 2018 census main report, with 2008 comparison. Country, region and district/city rows overlap and must not be summed together; cities are separate rows. Historical census counts, not current estimates.', 'items': _parse_pdf(p.stdout)}
