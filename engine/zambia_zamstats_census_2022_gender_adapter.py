"""Zambia ZamStats 2022 census numbers reproduced in its 2024 gender report."""
import release_runtime
import re
import subprocess
import fitz
URL = 'https://www.zamstats.gov.zm/wp-content/uploads/2025/11/Gender-Status-report-2024.pdf'
MARKER = 'Figure 2.2 Population Size by Sex and Province, Zambia 2022'

def _parse_pdf(data):
    if len(data) > 10000000 or not data.startswith(b'%PDF'):
        raise RuntimeError('Invalid Zambia report PDF')
    with fitz.open(stream=data, filetype='pdf') as doc:
        if len(doc) != 116:
            raise RuntimeError('Unexpected Zambia report page count')
        text = doc[23].get_text()
    if 'Figure 2.1; Population Size by Sex and rural/urban, Zambia 2022' not in text or MARKER not in text or 'Revised population summary Report' not in text:
        raise RuntimeError('Expected 2022 Zambia census charts missing')
    tail = text.split(MARKER, 1)[1]
    lines = [x.strip() for x in tail.splitlines() if x.strip()]
    numeric = [(i, s) for i, s in enumerate(lines) if re.fullmatch('\\d{1,3}(?:,\\d{3})+', s)]
    if len(numeric) != 29:
        raise RuntimeError('Unexpected chart values')
    idx = [i for i, s in numeric]
    v = [s for i, s in numeric]
    labels = lines[idx[-1] + 1:idx[-1] + 11]
    if len(labels) != 10 or labels[0] != 'Muchinga' or labels[-1] != 'Lusaka' or (len(set(labels)) != 10):
        raise RuntimeError('Unexpected provincial chart labels')
    geography = []
    for i, name in enumerate(['Total', 'Rural', 'Urban']):
        t, m, f = v[i * 3:i * 3 + 3]
        if int(m.replace(',', '')) + int(f.replace(',', '')) != int(t.replace(',', '')):
            raise RuntimeError('Sex totals inconsistent')
        geography.append({'geography': name, 'total_persons_raw': t, 'male_persons_raw': m, 'female_persons_raw': f})
    provinces = [{'province_label_raw': name, 'male_persons_raw': v[19 + i], 'female_persons_raw': v[9 + i]} for i, name in enumerate(labels)]
    for k in ['male', 'female']:
        if sum((int(row[k + '_persons_raw'].replace(',', '')) for row in provinces)) != int(geography[0][k + '_persons_raw'].replace(',', '')):
            raise RuntimeError('Provinces do not sum to total for ' + k)
    return (geography, provinces)

def population():
    p = release_runtime.run(['/usr/bin/curl', '-fsSL', '--max-time', '45', '--max-filesize', '10000000', URL], capture_output=True, timeout=50)
    if p.returncode:
        raise RuntimeError('ZamStats report request failed: ' + p.stderr.decode('utf-8', 'replace').strip())
    geography, provinces = _parse_pdf(p.stdout)
    return {'source': 'Zambia Statistics Agency', 'report': 'Gender Status Report 2020–2024', 'source_url': URL, 'pdf_page': 24, 'figures': ['2.1', '2.2'], 'reference_year': 2022, 'unit': 'persons', 'data_source_note': '2022 census revised population summary report, as reproduced in the gender report', 'geographies': geography, 'provinces': provinces, 'note': 'National total overlaps rural/urban and province figures. PDF text extraction truncates one province label to rth Western; raw text retained, confirm against image/source. Historical census, not current estimates.'}
