"""FAO FishStat 2026.1.0 global fisheries and aquaculture production quantities."""
import release_runtime
import argparse, csv, io, json, re, requests, zipfile
URL = 'https://www.fao.org/fishery/static/Data/GlobalProduction_2026.1.0.zip'
INFO = 'https://www.fao.org/statistics/events/events-detail/global-production.-march-2026-update/en'

def archive(local_file):
    if local_file:
        return zipfile.ZipFile(local_file)
    with requests.get(URL, stream=True, timeout=60) as r:
        r.raise_for_status()
        b = bytearray()
        for x in r.iter_content(65536):
            b.extend(x)
            if len(b) > 12000000:
                raise ValueError('unexpected archive size')
    return zipfile.ZipFile(io.BytesIO(b))

def rows(z, name, maxsize=60000000):
    info = z.getinfo(name)
    if info.file_size > maxsize:
        raise ValueError('member size exceeded')
    with io.TextIOWrapper(z.open(info), encoding='utf-8-sig', newline='') as f:
        yield from csv.DictReader(f)

def species(keyword, limit=40, local_file=None, *, offset=0):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 150 or (type(limit) is not int) or (not 1 <= limit <= 100) or (type(offset) is not int) or (not 0 <= offset <= 100000):
        raise ValueError('invalid filter')
    with archive(local_file) as z:
        matches = [{'code': r['3A_Code'], 'name': r['Name_En'], 'scientific_name': r['Scientific_Name']} for r in rows(z, 'CL_FI_SPECIES_GROUPS.csv') if keyword.casefold() in (r['Name_En'] + ' ' + r['Scientific_Name'] + ' ' + r['3A_Code']).casefold()]
    return {'source': local_file if local_file else URL, 'matched_count': len(matches), 'limit': limit, 'offset': offset, 'next_offset': offset + limit if offset + limit < len(matches) else None, 'records': matches[offset:offset + limit], 'note': 'The archive is re-read for each request; pin local_file to retain the same edition. Different editions may change ordering.' + (' Local archive provenance and version are unverified.' if local_file else '')}

def query(country, species_code, start, end, production_source='', limit=100, local_file=None, *, offset=0):
    if not re.fullmatch('[A-Z]{3}', country) or not re.fullmatch('[A-Z0-9]{3}', species_code):
        raise ValueError('invalid country or species code')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start, end, limit))) or not 1950 <= start <= end <= 2024 or (not 1 <= limit <= 500) or (type(offset) is not int) or (not 0 <= offset <= 1000000):
        raise ValueError('invalid year, limit or offset')
    if production_source not in ('', 'CAPTURE', 'FRESHWATER', 'BRACKISHWATER', 'MARINE'):
        raise ValueError('invalid production source')
    with archive(local_file) as z:
        c = [x for x in rows(z, 'CL_FI_COUNTRY_GROUPS.csv') if x['ISO3_Code'] == country]
        if len(c) != 1:
            raise ValueError('country not found or ambiguous')
        sp = [x for x in rows(z, 'CL_FI_SPECIES_GROUPS.csv') if x['3A_Code'] == species_code]
        if len(sp) != 1:
            raise ValueError('species not found or ambiguous')
        sources = {x['Code']: x['Name_En'] for x in rows(z, 'CL_FI_PRODUCTION_SOURCE_DET.csv')}
        areas = {x['Code']: x['Name_En'] for x in rows(z, 'CL_FI_WATERAREA_GROUPS.csv')}
        flags = {x['Symbol']: x['Name_En'] for x in rows(z, 'CL_FI_SYMBOL_SDMX.csv')}
        found = 0
        out = []
        for x in rows(z, 'Global_production_quantity.csv'):
            y = x['PERIOD']
            if x['COUNTRY.UN_CODE'] != c[0]['UN_Code'] or x['SPECIES.ALPHA_3_CODE'] != species_code or (not y.isdigit()) or (not start <= int(y) <= end) or (production_source and x['PRODUCTION_SOURCE_DET.CODE'] != production_source):
                continue
            found += 1
            if found > offset and len(out) < limit:
                out.append({**x, 'source_label': sources.get(x['PRODUCTION_SOURCE_DET.CODE']), 'area_label': areas.get(x['AREA.CODE']), 'status_label': flags.get(x['STATUS'])})
        return {'provider': None if local_file else 'FAO FishStat', 'source': local_file if local_file else URL, 'documentation': INFO, 'edition': None if local_file else 'Global Production 2026.1.0', 'country': country, 'country_name': c[0]['Name_En'], 'species': {'code': species_code, 'name': sp[0]['Name_En'], 'scientific_name': sp[0]['Scientific_Name']}, 'matched_count': found, 'limit': limit, 'offset': offset, 'next_offset': offset + limit if offset + limit < found else None, 'records': out, 'note': '每次重新读取数据包并本地截取；固定 local_file 可使用同一版本，不同版本顺序可能变化。MEASURE Q_tlw = tonnes live weight. Retain capture versus aquaculture, fishing area and status; do not conflate species with national totals or sum overlapping groups. Country-specific coverage and estimation notes are included in the source archive.' + (' Local archive provenance and version are unverified.' if local_file else '')}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='action', required=True)
    a = s.add_parser('species')
    a.add_argument('keyword')
    a.add_argument('--limit', type=int, default=40)
    a.add_argument('--local-file')
    a = s.add_parser('query')
    a.add_argument('country')
    a.add_argument('species')
    a.add_argument('start', type=int)
    a.add_argument('end', type=int)
    a.add_argument('--production-source', default='')
    a.add_argument('--limit', type=int, default=100)
    a.add_argument('--local-file')
    a = p.parse_args()
    v = species(a.keyword, a.limit, a.local_file) if a.action == 'species' else query(a.country, a.species, a.start, a.end, a.production_source, a.limit, a.local_file)
    print(json.dumps(v, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
