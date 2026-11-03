"""Read Timor-Leste central bank's historical Economic Statistics HTML table."""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
URL = 'https://bancocentral.tl/stats/economic/'
MAX_BYTES = 4 * 1024 * 1024

def _rows():
    with requests.get(URL, timeout=30, stream=True, allow_redirects=False) as response:
        response.raise_for_status()
        if response.is_redirect:
            raise RuntimeError('Unexpected redirect from official page')
        chunks = []
        size = 0
        for part in response.iter_content(65536):
            size += len(part)
            if size > MAX_BYTES:
                raise RuntimeError('Response exceeds 4 MiB')
            chunks.append(part)
    soup = BeautifulSoup(b''.join(chunks), 'html.parser')
    candidates = []
    for table in soup.find_all('table'):
        rows = []
        for tr in table.find_all('tr'):
            cells = tr.find_all(['td', 'th'], recursive=False)
            if any((c.has_attr('rowspan') or c.has_attr('colspan') for c in cells)):
                raise RuntimeError('Merged table cells require manual review')
            if cells:
                rows.append([' '.join(c.get_text(' ', strip=True).split()) for c in cells])
        if rows and rows[0][0] == 'Item' and (rows[0][-1] == 'Source') and all((re.fullmatch('\\d{4}', v) for v in rows[0][1:-1])):
            candidates.append(rows)
    if len(candidates) != 1:
        raise RuntimeError('Expected one identified economic statistics table')
    rows = candidates[0]
    head = rows[0]
    if any((len(row) != len(head) for row in rows[1:])):
        raise RuntimeError('Unexpected row width in source table')
    result = []
    group = ''
    for row in rows[1:]:
        if row[0] and (not any(row[1:])):
            group = row[0]
            continue
        if row[0]:
            result.append({'category': group, 'indicator': row[0], 'values': dict(zip(head[1:-1], row[1:-1])), 'original_source': row[-1]})
    return (head[1:-1], result)

def search(keyword='', limit=100, offset=0):
    if not isinstance(keyword, str) or len(keyword) > 200:
        raise ValueError('Invalid keyword')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 200) or isinstance(offset, bool) or (not isinstance(offset, int)) or (offset < 0):
        raise ValueError('Invalid offset or limit')
    years, rows = _rows()
    matches = [r for r in rows if keyword.casefold() in (r['indicator'] + ' ' + r['category']).casefold()]
    return {'source': 'Central Bank of Timor-Leste economic statistics', 'url': URL, 'years': years, 'query': keyword, 'total_matched': len(matches), 'offset': offset, 'items': matches[offset:offset + limit], 'note': 'Historical economic statistics table. Values and source labels are unchanged strings, not normalized numbers. Source page and indicator sources may be stale; verify interpretation, units, missing values and latest releases.'}
