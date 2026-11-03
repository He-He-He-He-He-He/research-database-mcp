"""Read 2024 Gambia preliminary census table 12, by local government area."""
import release_runtime
import re
import subprocess
import fitz
URL = 'https://www.gbosdata.org/downloads-file/544-2024-gphc-preliminary-report'
AREAS = ['Banjul', 'Kanifing', 'Brikama', 'Mansakonko', 'Kerewan', 'Kuntaur', 'Janjanbureh', 'Basse']
TITLE = 'Table 12: Population Distribution by Sex and LGA'

def _parse_pdf(data):
    if len(data) > 6000000 or not data.startswith(b'%PDF'):
        raise RuntimeError('Invalid GBoS census PDF')
    with fitz.open(stream=data, filetype='pdf') as doc:
        if len(doc) != 25:
            raise RuntimeError('Unexpected GBoS report pagination')
        text = doc[21].get_text()
    if TITLE not in text or 'GAMBIA BUREAU OF STATISTICS' not in text:
        raise RuntimeError('Census table not found')
    part = text.split(TITLE, 1)[0]
    lines = [line.strip() for line in part.splitlines() if line.strip()]
    if lines[2:10] != AREAS or not all((x in lines for x in ['Male', 'Female', 'Total', 'LGA'])):
        raise RuntimeError('Unexpected census table headings or locations')
    vals = [x for x in lines if re.fullmatch('[\\d,]+(?:\\.\\d+)?', x)]
    if len(vals) != 54:
        raise RuntimeError('Unexpected census table columns')
    out = []
    for i, area in enumerate(AREAS + ['Total']):
        j = i if i < 8 else 16
        k = i + 18 if i < 8 else 34
        n = i + 36 if i < 8 else 44
        pc = i + 8 if i < 8 else 17
        fc = i + 26 if i < 8 else 35
        tc = i + 45 if i < 8 else 53
        male, female, total = (vals[j], vals[k], vals[n])
        if int(male.replace(',', '')) + int(female.replace(',', '')) != int(total.replace(',', '')):
            raise RuntimeError('Census sex totals do not agree for ' + area)
        out.append({'area': area, 'male_persons_raw': male, 'male_percent_raw': vals[pc], 'female_persons_raw': female, 'female_percent_raw': vals[fc], 'total_persons_raw': total, 'total_percent_raw': vals[tc]})
    if sum((int(x['total_persons_raw'].replace(',', '')) for x in out[:-1])) != int(out[-1]['total_persons_raw'].replace(',', '')):
        raise RuntimeError('LGA sum does not agree with national total')
    return out

def areas():
    p = release_runtime.run(['/usr/bin/curl', '-fsSL', '--max-time', '45', '--max-filesize', '6000000', URL], capture_output=True, timeout=50)
    if p.returncode:
        raise RuntimeError('GBoS PDF request failed: ' + p.stderr.decode('utf-8', 'replace').strip())
    return {'source': 'Gambia Bureau of Statistics', 'report': 'The Gambia 2024 Population and Housing Census Preliminary Report', 'source_url': URL, 'table': TITLE, 'pdf_page': 22, 'printed_page': 15, 'reference_year': 2024, 'status': 'preliminary', 'units': 'population: persons; shares: percent of population within the area', 'note': 'Preliminary count, not a current estimate; national total and local areas overlap. Percentage figures as printed, subject to rounding. Consult later releases for revisions.', 'items': _parse_pdf(p.stdout)}
