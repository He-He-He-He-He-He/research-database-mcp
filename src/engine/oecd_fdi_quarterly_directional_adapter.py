"""OECD directional quarterly aggregate foreign direct investment flows."""
import release_runtime
import csv, io, re, requests
BASE = 'https://sdmx.oecd.org/public/rest/data/OECD.DAF.INV,DSD_FDI@DF_FDI_FLOW_AGGR,1.0/'
DOC = 'https://data-explorer.oecd.org/vis?df%5Bag%5D=OECD.DAF.INV&df%5Bid%5D=DSD_FDI%40DF_FDI_FLOW_AGGR&df%5Bvs%5D=1.0'

def query(country, direction, start, end):
    if not isinstance(country, str) or not re.fullmatch('[A-Za-z]{3}', country):
        raise ValueError('country must be three letters')
    if direction not in ('inward', 'outward'):
        raise ValueError('direction must be inward or outward')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start, end))) or not 1900 <= start <= end <= 2100:
        raise ValueError('invalid years')
    country = country.upper()
    principle = {'inward': 'DI', 'outward': 'DO'}[direction]
    parts = [country, 'T_FA_F', 'USD_EXC', principle, 'NET_FDI', 'ALL', 'D', 'S1', 'W', 'IMC', '_T', 'Q', 'AGGR']
    r = requests.get(BASE + '.'.join(parts), params={'startPeriod': start, 'endPeriod': end, 'format': 'csvfile'}, timeout=40)
    if r.status_code == 204 or (r.status_code == 404 and r.text.strip() in ('NoRecordsFound', 'NoResultsFound')):
        rows = []
    else:
        r.raise_for_status()
        reader = csv.DictReader(io.StringIO(r.text))
        needed = {'REF_AREA', 'MEASURE', 'UNIT_MEASURE', 'MEASURE_PRINCIPLE', 'ACCOUNTING_ENTRY', 'TYPE_ENTITY', 'FDI_COMP', 'SECTOR', 'COUNTERPART_AREA', 'LEVEL_COUNTERPART', 'ACTIVITY', 'FREQ', 'FDI_COLLECTION_ID', 'TIME_PERIOD', 'OBS_VALUE', 'OBS_STATUS', 'UNIT_MULT', 'CURRENCY'}
        if not reader.fieldnames or not needed.issubset(reader.fieldnames):
            raise ValueError('unexpected OECD CSV')
        rows = list(reader)
        dims = dict(zip(['REF_AREA', 'MEASURE', 'UNIT_MEASURE', 'MEASURE_PRINCIPLE', 'ACCOUNTING_ENTRY', 'TYPE_ENTITY', 'FDI_COMP', 'SECTOR', 'COUNTERPART_AREA', 'LEVEL_COUNTERPART', 'ACTIVITY', 'FREQ', 'FDI_COLLECTION_ID'], parts))
        dims.update({'UNIT_MULT': '6', 'CURRENCY': 'USD'})
        if any((any((x.get(k) != v for k, v in dims.items())) for x in rows)):
            raise ValueError('unexpected OECD dimensions')
    return {'source': r.url, 'documentation': DOC, 'country': country, 'direction': direction, 'records': rows, 'note': 'Quarterly net directional FDI financial flows, USD millions (UNIT_MULT=6), all entities, all counterpart economies. Not inward/outward positions, project approvals, greenfield-only investment, or aggregate GDP. Negative flows can occur due to disinvestment or repayments; preserve them and statuses. Annual values are not fabricated by summing quarters. Countries may report only asset/liability data rather than directional flows; empty result is not zero. Rows retain source order, which is not necessarily chronological; use TIME_PERIOD.'}
