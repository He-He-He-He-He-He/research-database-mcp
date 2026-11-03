"""Global Carbon Project fossil CO2 national 2024v18, archived 2024-11-13."""
import release_runtime
import argparse
import csv
import hashlib
import io
import json
import re
import requests
BASE = 'https://zenodo.org/api/records/14106218/files/'
RECORD = 'https://zenodo.org/records/14106218'
FILES = {'emissions': ('GCB2024v18_MtCO2_flat.csv', '70dac1843444b14655bf756c70c1f04a', 'ISO 3166-1 alpha-3'), 'sources': ('GCB2024v18_sources_flat.csv', 'b73b61013613ed685dfc46dba75440d8', 'ISO 3166-1 alpha-3'), 'population': ('GCB2024v18_population_flat.csv', '63419473c8af502e9c413578424b4c94', 'ISO3')}
META = ('GCB2024v18_MtCO2_flat_metadata.json', '0279ab0885a576c2811ca9cef1bbc61d')
MAX_BYTES = 12000000

def _fetch(filename, checksum):
    url = BASE + filename + '/content'
    with requests.get(url, timeout=40, stream=True) as r:
        r.raise_for_status()
        raw = bytearray()
        for b in r.iter_content(65536):
            raw.extend(b)
            if len(raw) > MAX_BYTES:
                raise ValueError('file exceeds size limit')
    if hashlib.md5(raw).hexdigest() != checksum:
        raise ValueError('file differs from Zenodo published checksum')
    return bytes(raw)

def query(iso3, start=2020, end=2023, kind='emissions', limit=100):
    if not isinstance(iso3, str) or not re.fullmatch('[A-Z]{3}', iso3):
        raise ValueError('ISO3 must be uppercase')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start, end, limit))) or not 1750 <= start <= end <= 2024 or (not 1 <= limit <= 500) or (kind not in FILES):
        raise ValueError('invalid range or kind')
    name, md5, code = FILES[kind]
    reader = csv.DictReader(io.StringIO(_fetch(name, md5).decode('utf-8-sig'), newline=''))
    if not reader.fieldnames or code not in reader.fieldnames or 'Year' not in reader.fieldnames:
        raise ValueError('unexpected source columns')
    out = []
    count = 0
    for row in reader:
        if row[code] != iso3:
            continue
        try:
            y = int(row['Year'])
        except (ValueError, TypeError):
            continue
        if not start <= y <= end:
            continue
        count += 1
        if len(out) < limit:
            out.append(row)
    meta = json.loads(_fetch(*META)) if kind == 'emissions' else None
    return {'source': BASE + name + '/content', 'record': RECORD, 'edition': '2024v18', 'published': '2024-11-13', 'license': 'CC BY 4.0', 'kind': kind, 'iso3': iso3, 'start': start, 'end': end, 'matched_count': count, 'returned': len(out), 'records': out, 'metadata': meta, 'note': 'Peer-reviewed research data, not a government release. Total/fuel emissions are million tonnes CO2, per-capita column tonnes CO2/person; population is people. This is fossil and industry CO2, not total GHG or a complete land-use-inclusive budget. Values, blanks and original source strings are preserved; annual national data may stop before 2024.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('iso3')
    p.add_argument('--start', type=int, default=2020)
    p.add_argument('--end', type=int, default=2023)
    p.add_argument('--kind', choices=FILES, default='emissions')
    p.add_argument('--limit', type=int, default=100)
    a = p.parse_args()
    print(json.dumps(query(a.iso3, a.start, a.end, a.kind, a.limit), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
