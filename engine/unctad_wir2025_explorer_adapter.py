"""UNCTAD 2025 FDI explorer official-hosted static data with unit conflict warning."""
import release_runtime
import argparse
import json
import requests
URL = 'https://unctad-infovis.github.io/2025-fdi_explorer/assets/data/2025-fdi_explorer.json'
REPORT = 'https://unctad.org/system/files/official-document/wir2025_annex-tables_en.pdf'
EXPLAINER = 'https://unctad.org/news/explore-global-investment-data-and-changing-trends'
MAX_BYTES = 2000000

def query(keyword, direction='inflows', start=1990, end=2024, limit=30):
    if not isinstance(keyword, str) or not 2 <= len(keyword.strip()) <= 100:
        raise ValueError('invalid search keyword')
    if direction not in ('inflows', 'outflows'):
        raise ValueError('invalid direction')
    if any((isinstance(v, bool) or not isinstance(v, int) or (not 1990 <= v <= 2024) for v in (start, end))) or start > end:
        raise ValueError('invalid years')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 100):
        raise ValueError('invalid limit')
    with requests.get(URL, timeout=25, stream=True) as r:
        r.raise_for_status()
        raw = bytearray()
        for part in r.iter_content(65536):
            raw.extend(part)
            if len(raw) > MAX_BYTES:
                raise ValueError('response exceeds size limit')
    d = json.loads(raw)
    rows = d.get('fdi_' + direction)
    if not isinstance(rows, list):
        raise ValueError('unexpected data schema')
    matches = []
    for row in rows:
        name = row.get('Region/economy')
        if isinstance(name, str) and keyword.casefold() in name.casefold():
            matches.append(row)
    out = []
    for row in matches[:limit]:
        out.append({'name': row.get('Region/economy'), 'type': row.get('type'), 'level': row.get('level'), 'raw_observations': {str(y): row.get(str(y)) for y in range(start, end + 1)}})
    return {'source': URL, 'visualization_page': 'https://unctad-infovis.github.io/2025-fdi_explorer/', 'explainer': EXPLAINER, 'report_annex': REPORT, 'report_published': '2025-06-19', 'explainer_published': '2025-10-07', 'direction': direction, 'matched_count': len(matches), 'returned': len(out), 'records': out, 'unit_warning': 'Visualization labels data thousands of dollars; 2025 report Annex 1 labels millions. World 2024 raw 1508803.342 and Egypt 46578 match the report values rounded in millions. Source labels conflict: preserve raw values, do not automatically convert; verify each use against report. Explorer published after June 2025 and may have revisions.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('keyword')
    p.add_argument('--direction', choices=['inflows', 'outflows'], default='inflows')
    p.add_argument('--start', type=int, default=1990)
    p.add_argument('--end', type=int, default=2024)
    p.add_argument('--limit', type=int, default=30)
    a = p.parse_args()
    print(json.dumps(query(a.keyword, a.direction, a.start, a.end, a.limit), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
