"""Namibia Statistics Agency: preliminary census comparison, table 3.1 only."""
import release_runtime
import re
import subprocess
import fitz
URL = 'https://www.nsa.org.na/wp-content/uploads/2024/07/Preliminary-Report-2023-Population-and-Housing-Census_compressed.pdf'
TITLE = 'Table 3.1: Population percentage change by region, Namibia 2011 and 2023 Censuses'
REGIONS = {'Namibia', '//Kharas', 'Erongo', 'Hardap', 'Kavango East', 'Kavango West', 'Khomas', 'Kunene', 'Ohangwena', 'Omaheke', 'Omusati', 'Oshana', 'Oshikoto', 'Otjozondjupa', 'Zambezi'}

def _parse_pdf(data):
    if len(data) > 15000000 or not data.startswith(b'%PDF'):
        raise RuntimeError('Invalid or oversized Namibia census PDF')
    with fitz.open(stream=data, filetype='pdf') as doc:
        if len(doc) < 23 or len(doc) > 200:
            raise RuntimeError('Unexpected Namibia census PDF length')
        text = doc[22].get_text()
    if TITLE not in text:
        raise RuntimeError('Expected Namibia census table missing from PDF page 23')
    lines = [x.strip() for x in text.split(TITLE, 1)[1].splitlines() if x.strip()]
    rows = []
    for i, name in enumerate(lines):
        if name not in REGIONS:
            continue
        fields = lines[i + 1:i + 6]
        if len(fields) != 5 or not all((re.fullmatch('\\d[\\d ]*', fields[n]) for n in (0, 2))) or (not all((re.fullmatch('\\d+\\.\\d+', fields[n]) for n in (1, 3, 4)))):
            raise RuntimeError('Unexpected Namibia census row structure: ' + name)
        rows.append(dict(region=name, population_2011_raw=fields[0], share_2011_percent_raw=fields[1], population_2023_raw=fields[2], share_2023_percent_raw=fields[3], change_2011_2023_percent_raw=fields[4]))
    if len(rows) != len(REGIONS) or {r['region'] for r in rows} != REGIONS:
        raise RuntimeError('Missing or duplicate Namibia census regions')
    return rows

def regions():
    """Read official preliminary Table 3.1, returning original numeric strings."""
    p = release_runtime.run(['/usr/bin/curl', '-fsSL', '--max-time', '45', '--max-filesize', '15000000', URL], capture_output=True, timeout=50)
    if p.returncode:
        raise RuntimeError('Namibia NSA PDF download failed: ' + p.stderr.decode('utf-8', 'replace').strip())
    return {'source': 'Namibia Statistics Agency', 'report_title': '2023 Population & Housing Census Preliminary Report', 'report_url': URL, 'table': TITLE, 'pdf_page': 23, 'units': 'population: persons; population share and percentage change: percent', 'data_status': 'preliminary', 'note': '2011 and 2023 census comparison. National total overlaps 14 regions and must not be added. Figures and rates are returned as printed; consult the official final census report for revisions and methodology.', 'items': _parse_pdf(p.stdout)}
