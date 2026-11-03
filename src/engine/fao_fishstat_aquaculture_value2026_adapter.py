"""FAO FishStat 2026 aquaculture nominal production value by species and environment."""
import release_runtime
import argparse, io, json, re, requests, zipfile
from fao_fishstat_global_production2026_adapter import rows
URL = 'https://www.fao.org/fishery/static/Data/Aquaculture_2026.1.0.zip'
INFO = 'https://www.fao.org/statistics/events/events-detail/global-production.-march-2026-update/en'

def query(country, species, start, end, environment='', area='', limit=100, local_file=None):
    if not re.fullmatch('[A-Z]{3}', country) or not re.fullmatch('[A-Z0-9]{3}', species):
        raise ValueError('invalid country or species')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start, end, limit))) or not 1984 <= start <= end <= 2024 or (not 1 <= limit <= 500):
        raise ValueError('invalid years or limit')
    if environment not in ('', 'IN', 'BW', 'MA', 'AL') or (area and (not re.fullmatch('[0-9]{2}', area))):
        raise ValueError('invalid environment or area')
    if local_file:
        z = zipfile.ZipFile(local_file)
    else:
        with requests.get(URL, stream=True, timeout=45) as r:
            r.raise_for_status()
            b = bytearray()
            for c in r.iter_content(65536):
                b.extend(c)
                if len(b) > 8000000:
                    raise ValueError('unexpected archive size')
        z = zipfile.ZipFile(io.BytesIO(b))
    try:
        c = [x for x in rows(z, 'CL_FI_COUNTRY_GROUPS.csv') if x['ISO3_Code'] == country]
        sp = [x for x in rows(z, 'CL_FI_SPECIES_GROUPS.csv') if x['3A_Code'] == species]
        if len(c) != 1 or len(sp) != 1:
            raise ValueError('unknown or ambiguous country/species')
        areas = {x['Code']: x['Name_En'] for x in rows(z, 'CL_FI_WATERAREA_GROUPS.csv')}
        env = {x['Code']: x['Name_En'] for x in rows(z, 'CL_FI_PRODENVIRONMENT.csv')}
        flags = {x['Symbol']: x['Name_En'] for x in rows(z, 'CL_FI_SYMBOL_SDMX.csv')}
        out = []
        count = 0
        for x in rows(z, 'Aquaculture_Value.csv'):
            y = x['PERIOD']
            if x['COUNTRY.UN_CODE'] != c[0]['UN_Code'] or x['SPECIES.ALPHA_3_CODE'] != species or (not y.isdigit()) or (not start <= int(y) <= end) or (area and x['AREA.CODE'] != area) or (environment and x['ENVIRONMENT.ALPHA_2_CODE'] != environment):
                continue
            count += 1
            if len(out) < limit:
                out.append({**x, 'area_label': areas.get(x['AREA.CODE']), 'environment_label': env.get(x['ENVIRONMENT.ALPHA_2_CODE']), 'status_label': flags.get(x['STATUS'])})
        return {'provider': None if local_file else 'FAO FishStat', 'source': local_file if local_file else URL, 'documentation': INFO, 'edition': None if local_file else 'Aquaculture 2026.1.0', 'country': country, 'country_name': c[0]['Name_En'], 'species': {'code': species, 'name': sp[0]['Name_En'], 'scientific_name': sp[0]['Scientific_Name']}, 'unit': 'thousand current US dollars', 'matched_count': count, 'records': out, 'note': 'Nominal aquaculture production value converted from local currency; value is thousands of US dollars, not quantities or profit. Record status and environment; currency conversion, country coverage and imputation may affect comparability. Country metadata and caveats are inside the ZIP.' + (' Local archive provenance and version are unverified.' if local_file else '')}
    finally:
        z.close()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('country')
    p.add_argument('species')
    p.add_argument('start', type=int)
    p.add_argument('end', type=int)
    p.add_argument('--environment', default='')
    p.add_argument('--area', default='')
    p.add_argument('--limit', type=int, default=100)
    p.add_argument('--local-file')
    a = p.parse_args()
    print(json.dumps(query(a.country, a.species, a.start, a.end, a.environment, a.area, a.limit, a.local_file), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
