"""UNCTAD World Investment Report 2024 data explorer historical edition."""
import release_runtime
import argparse
import json
import requests
URL = 'https://unctad-infovis.github.io/2024-wir_report/assets/data/2024-wir_report_figure1.json'
REPORT = 'https://unctad.org/system/files/official-document/wir2024_annex-1_en.pdf'
EXPLAINER = 'https://unctad.org/publication/world-investment-report-2024'
MAX_BYTES = 2000000

def query(keyword, direction='inflows', start=1990, end=2023, limit=30):
    if not isinstance(keyword, str) or not 2 <= len(keyword.strip()) <= 100:
        raise ValueError('invalid search keyword')
    if direction not in ('inflows', 'outflows'):
        raise ValueError('invalid direction')
    if any((isinstance(v, bool) or not isinstance(v, int) or (not 1990 <= v <= 2023) for v in (start, end))) or start > end:
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
    return {'source': URL, 'visualization_page': 'https://unctad-infovis.github.io/2024-wir_report/', 'explainer': EXPLAINER, 'report_annex': REPORT, 'report_published': '2024-06-20', 'direction': direction, 'matched_count': len(matches), 'returned': len(out), 'records': out, 'unit_warning': 'Raw values retained; visualization and 2024 report annex use millions of US dollars. World 2023 and Egypt 2023 values match the 2024 report annex after rounding; verify other rows against the original report. Current visualization file historical integrity and release timing are not independently established.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('keyword')
    p.add_argument('--direction', choices=['inflows', 'outflows'], default='inflows')
    p.add_argument('--start', type=int, default=1990)
    p.add_argument('--end', type=int, default=2023)
    p.add_argument('--limit', type=int, default=30)
    a = p.parse_args()
    print(json.dumps(query(a.keyword, a.direction, a.start, a.end, a.limit), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
