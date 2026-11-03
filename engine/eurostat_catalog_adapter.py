"""Eurostat official table-of-contents search and SDMX structure metadata.

Documentation: https://ec.europa.eu/eurostat/web/user-guides/data-browser/api-data-access/api-getting-started/catalogue-api
Use eurostat_adapters.query_dataset for bounded statistical observations.
"""
import release_runtime
import csv, io, re, subprocess, xml.etree.ElementTree as ET
BASE = 'https://ec.europa.eu/eurostat/api/dissemination'
MAX_BYTES = 12000000

def _get(path):
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '40', '--max-filesize', str(MAX_BYTES), BASE + path], capture_output=True, timeout=45)
    if r.returncode:
        raise RuntimeError('Eurostat request failed: ' + r.stderr.decode('utf-8', 'replace')[:500])
    if len(r.stdout) > MAX_BYTES:
        raise ValueError('Eurostat response exceeds 12 MB')
    return r.stdout.decode('utf-8-sig')

def search(keyword, limit=30, offset=0):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 200:
        raise ValueError('invalid keyword')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (offset, limit))) or offset < 0 or (not 1 <= limit <= 100):
        raise ValueError('offset must be nonnegative and limit 1 to 100')
    path = '/catalogue/toc/txt?lang=en'
    raw = _get(path)
    reader = csv.DictReader(io.StringIO(raw), delimiter='\t')
    if not reader.fieldnames or not {'title', 'code', 'type'}.issubset(reader.fieldnames):
        raise ValueError('unexpected Eurostat catalog format')
    rows = []
    total = 0
    for row in reader:
        if row['type'] not in ('dataset', 'table'):
            continue
        if keyword.casefold() in (row['title'] + ' ' + row['code']).casefold():
            total += 1
            if offset <= total - 1 < offset + limit:
                rows.append({k: v.strip() if isinstance(v, str) else v for k, v in row.items()})
    return {'source': BASE + path, 'matched': total, 'offset': offset, 'limit': limit, 'results': rows}

def structure(dataset):
    if not isinstance(dataset, str) or not re.fullmatch('[A-Za-z0-9_]{1,80}', dataset):
        raise ValueError('invalid dataset code')
    path = '/sdmx/2.1/dataflow/ESTAT/' + dataset + '/1.0?references=descendants'
    xml = _get(path)
    ET.fromstring(xml)
    return {'source': BASE + path, 'sdmx_xml': xml, 'note': 'Original Eurostat dataflow, structure and reference code lists. Dataset-specific metadata applies.'}
