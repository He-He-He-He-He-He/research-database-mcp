"""Zimbabwe ZIMSTAT 2022 census population and households, by province."""
import release_runtime
import re
import subprocess
import fitz
URL = 'https://www.zimstat.co.zw/wp-content/uploads//Census/2022_Population_Distribution_by_District_Ward_SexandHouseholds_23012023.pdf'
PAGE = 'https://zimstat.co.zw/population-census/'
TITLE = 'Population Distribution by Province, Sex and Number of Households'
NAMES = {'Bulawayo', 'Manicaland', 'Mashonaland Central', 'Mashonaland East', 'Mashonaland West', 'Matabeleland North', 'Matabeleland South', 'Midlands', 'Masvingo', 'Harare', 'Total'}

def _parse_pdf(data):
    if len(data) > 8000000 or not data.startswith(b'%PDF'):
        raise RuntimeError('Invalid ZIMSTAT census PDF')
    with fitz.open(stream=data, filetype='pdf') as doc:
        if len(doc) != 106:
            raise RuntimeError('Unexpected ZIMSTAT census PDF pagination')
        text = doc[5].get_text()
    if TITLE not in text:
        raise RuntimeError('Expected province table missing')
    part = text.split(TITLE, 1)[1]
    lines = [x.strip() for x in part.splitlines() if x.strip()]
    if lines[:5] != ['Province', 'Male', 'Female', 'Total', 'Households'] or len(lines) != 60:
        raise RuntimeError('Unexpected ZIMSTAT census table structure')
    out = []
    for i in range(11):
        name, *v = lines[5 + i * 5:10 + i * 5]
        if name not in NAMES or not all((re.fullmatch('\\d{1,3}(?:,\\d{3})*', x) for x in v)):
            raise RuntimeError('Unexpected province census row')
        if int(v[0].replace(',', '')) + int(v[1].replace(',', '')) != int(v[2].replace(',', '')):
            raise RuntimeError('Population total inconsistent for ' + name)
        out.append({'province': name, 'male_persons_raw': v[0], 'female_persons_raw': v[1], 'total_persons_raw': v[2], 'households_raw': v[3]})
    if {r['province'] for r in out} != NAMES or out[-1]['province'] != 'Total':
        raise RuntimeError('Missing/duplicate census provinces')
    if sum((int(x['total_persons_raw'].replace(',', '')) for x in out[:-1])) != int(out[-1]['total_persons_raw'].replace(',', '')):
        raise RuntimeError('Province population sum mismatch')
    return out

def provinces():
    p = release_runtime.run(['/usr/bin/curl', '-fsSL', '--max-time', '45', '--max-filesize', '8000000', URL], capture_output=True, timeout=50)
    if p.returncode:
        raise RuntimeError('ZIMSTAT census PDF request failed: ' + p.stderr.decode('utf-8', 'replace').strip())
    return {'source': 'Zimbabwe National Statistics Agency (ZIMSTAT)', 'publication_page': PAGE, 'source_url': URL, 'table': TITLE, 'pdf_page': 6, 'reference_year': 2022, 'unit': 'population: persons; households: households', 'note': 'Official 2022 population and housing census. Province totals overlap national total; avoid double counting. Historical census counts, not current estimates.', 'items': _parse_pdf(p.stdout)}
