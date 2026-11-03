"""Read five district rows from Tunisia INS RGPH 2024 demographic bulletin."""
import release_runtime
import re, subprocess, fitz
PAGE = 'https://www.ins.tn/publication/recensement-general-de-la-population-et-de-lhabitat-2024'
URL = 'https://www.ins.tn/sites/default/files-ftp3/files/publication/pdf/Bilan_D%C3%A9mographique.pdf'

def districts():
    p = release_runtime.run(['/usr/bin/curl', '-fsSL', '--max-time', '45', '--max-filesize', '15000000', URL], capture_output=True, timeout=50)
    if p.returncode:
        raise RuntimeError('Tunisia INS PDF request failed: ' + p.stderr.decode('utf-8', 'replace').strip())
    if len(p.stdout) > 15000000 or not p.stdout.startswith(b'%PDF'):
        raise RuntimeError('Invalid INS PDF')
    with fitz.open(stream=p.stdout, filetype='pdf') as d:
        if len(d) < 19 or len(d) > 150:
            raise RuntimeError('Unexpected census report pagination')
        text = d[18].get_text(sort=True)
    if 'Répartition de la population selon les districts en Tunisie' not in text or '6 novembre 2024' not in text:
        raise RuntimeError('Expected census table not found')
    data = []
    for line in text.splitlines():
        m = re.fullmatch('\\s*(District\\s+[1-5]|Total)\\s+(\\d+)\\s+([\\d.]+%)\\s*', line)
        if m:
            data.append({'geography_raw': m.group(1), 'population_persons_raw': m.group(2), 'share_raw': m.group(3), 'raw_line': line.strip()})
    if len(data) != 6 or {r['geography_raw'] for r in data} != {'District 1', 'District 2', 'District 3', 'District 4', 'District 5', 'Total'}:
        raise RuntimeError('Census table rows missing or ambiguous')
    if sum((int(r['population_persons_raw']) for r in data if r['geography_raw'] != 'Total')) != int(next((r['population_persons_raw'] for r in data if r['geography_raw'] == 'Total'))):
        raise RuntimeError('District count consistency check failed')
    return {'source': 'Institut National de la Statistique Tunisie', 'publication_page': PAGE, 'report_url': URL, 'report_title': 'RGPH 2024: Bilan Démographique', 'physical_pdf_page': 19, 'reference_date': '2024-11-06', 'unit': 'persons and percent of national total', 'items': data, 'note': 'Official report is described as first results; district rows partition national total, not governorates. Shares are rounded; total overlaps districts and must not be added. This table contains 2024 census figures only; consult original report for definitions and later revisions.'}
