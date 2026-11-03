"""Indian Ocean Tuna Commission retained catches 1950–2025, 2026-08 release."""
import release_runtime
import csv
import io
import requests
import zipfile
URL = 'https://iotc.org/sites/default/files/documents/2026/08/IOTC-DATASETS-2026-08-13-RC-RAW-1950-2025.zip'
DOC = 'https://iotc.org/data/datasets/latest/NC/ALL'

def data(year=None, fleet='', species='', offset=0, limit=20):
    if year is not None and (not isinstance(year, int) or isinstance(year, bool) or (not 1950 <= year <= 2025)):
        raise ValueError('year must be 1950–2025')
    if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:
        raise ValueError('invalid offset')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 200):
        raise ValueError('limit must be 1–200')
    r = requests.get(URL, timeout=60)
    r.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        names = [n for n in z.namelist() if n.endswith('.csv')]
        if len(names) != 1:
            raise ValueError('unexpected source archive')
        with z.open(names[0]) as raw:
            reader = csv.DictReader(io.TextIOWrapper(raw, encoding='utf-8-sig', newline=''))
            if not {'YEAR', 'FLEET_CODE', 'SPECIES_CODE', 'CATCH'}.issubset(reader.fieldnames or []):
                raise ValueError('unexpected source fields')
            total = 0
            rows = []
            for row in reader:
                if year is not None and row['YEAR'] != str(year):
                    continue
                if fleet and row['FLEET_CODE'].casefold() != fleet.strip().casefold():
                    continue
                if species and row['SPECIES_CODE'].casefold() != species.strip().casefold():
                    continue
                if offset <= total < offset + limit:
                    rows.append(row)
                total += 1
    return {'source': URL, 'documentation': DOC, 'version': '2026-08-13', 'unit': 'metric tonnes live-weight equivalent', 'total_matches': total, 'offset': offset, 'limit': limit, 'rows': rows, 'notes': ['Indian Ocean retained catch data compiled from national and industry reports; fishing fleet code is an IOTC source code, not necessarily an ISO country code.', 'CATCH is retained fish in live-weight-equivalent metric tonnes, not fishing effort, total marine production, stock size or a measure of unreported bycatch.', 'Some reporting groups are not fully disaggregated by species or gear; do not blindly sum overlapping aggregate and detailed categories.', 'Fixed 2026-08-13 snapshot through 2025; source updates irregularly and figures may be revised. Public-domain data, attribution to IOTC required.']}
