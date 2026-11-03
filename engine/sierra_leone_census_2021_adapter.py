"""Sierra Leone official 2021 mid-term census final district table."""
import release_runtime
import re
import subprocess
import fitz
URL = 'https://www.statistics.sl/images/StatisticsSL/Documents/Census/2021_MTPHC_Final_Results_Tables_ByDistrict.pdf'
REGIONS = {'EASTERN', 'NORTH EAST', 'NORTH WEST', 'SOUTH', 'WESTERN'}

def _parse_pdf(data):
    if not data.startswith(b'%PDF') or len(data) > 5000000:
        raise RuntimeError('Invalid or oversized census PDF')
    with fitz.open(stream=data, filetype='pdf') as doc:
        if len(doc) != 3:
            raise RuntimeError('Unexpected Sierra Leone census report page count')
        text = doc[1].get_text()
    marker = 'POPULATION BY DISTRICT'
    if '2021 DIGITAL MID-TERM CENSUS FINAL RESULTS BY DISTRICT' not in text or marker not in text:
        raise RuntimeError('Expected district table absent')
    lines = [s.strip() for s in text.split(marker, 1)[1].splitlines() if s.strip()]
    if lines[:6] != ['REGION', 'DISTRICT', 'MALE', 'FEMALE', 'TOTAL', 'SEX RATIO']:
        raise RuntimeError('Unexpected district table header')
    i, region, rows = (6, None, [])
    while i < len(lines):
        if lines[i] in REGIONS:
            region = lines[i]
            i += 1
        if i + 4 >= len(lines):
            raise RuntimeError('Truncated district table')
        name = lines[i]
        vals = lines[i + 1:i + 5]
        i += 5
        if not region or not all((re.fullmatch('\\d{1,3}(?:,\\d{3})*', x) for x in vals[:3])) or (not re.fullmatch('\\d+\\.\\d+', vals[3])):
            raise RuntimeError('Unexpected census table row: ' + name)
        if int(vals[0].replace(',', '')) + int(vals[1].replace(',', '')) != int(vals[2].replace(',', '')):
            raise RuntimeError('District total inconsistent: ' + name)
        rows.append({'region': region if name != 'NATIONAL TOTAL' else None, 'district_or_total': name, 'male_persons_raw': vals[0], 'female_persons_raw': vals[1], 'total_persons_raw': vals[2], 'sex_ratio_raw': vals[3]})
    if len(rows) != 22 or sum((x['district_or_total'] == 'REGIONAL TOTAL' for x in rows)) != 5 or rows[-1]['district_or_total'] != 'NATIONAL TOTAL':
        raise RuntimeError('Unexpected districts or totals')
    district_sum = sum((int(x['total_persons_raw'].replace(',', '')) for x in rows if x['district_or_total'] not in ('REGIONAL TOTAL', 'NATIONAL TOTAL')))
    if district_sum != int(rows[-1]['total_persons_raw'].replace(',', '')):
        raise RuntimeError('District sum differs from national total')
    return rows

def districts():
    p = release_runtime.run(['/usr/bin/curl', '-fsSL', '--max-time', '45', '--max-filesize', '5000000', URL], capture_output=True, timeout=50)
    if p.returncode:
        raise RuntimeError('Sierra Leone statistics PDF request failed: ' + p.stderr.decode('utf-8', 'replace').strip())
    return {'source': 'Statistics Sierra Leone', 'publication_title': '2021 Digital Mid-Term Census Final Results by District', 'report_url': URL, 'pdf_page': 2, 'reference_year': 2021, 'unit': 'persons; sex ratio: males per 100 females', 'note': 'Official final 2021 mid-term census results, not current estimates. District, regional and national totals overlap and should not be summed together.', 'items': _parse_pdf(p.stdout)}
