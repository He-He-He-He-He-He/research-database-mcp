"""FAO FishStat 2026.1.0 annual fisheries and aquaculture primary sector employment."""
import release_runtime
import argparse, csv, io, json, re, zipfile, requests
URL = 'https://www.fao.org/fishery/static/Data/FI_Employment_2026.1.0.zip'
INFO = 'https://www.fao.org/statistics/data-dissemination/fishery-and-aquaculture/'

def query(country, start, end, workarea='', occupation='', gender='', limit=100, local_file=None, *, offset=0):
    if not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('country must be ISO3')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start, end, limit))) or not 1950 <= start <= end <= 2100 or (not 1 <= limit <= 500) or (type(offset) is not int) or (not 0 <= offset <= 1000000):
        raise ValueError('invalid bounds')
    if any((not isinstance(x, str) or len(x) > 8 for x in (workarea, occupation, gender))):
        raise ValueError('invalid dimension filters')
    if local_file:
        z = zipfile.ZipFile(local_file)
    else:
        with requests.get(URL, stream=True, timeout=45) as r:
            r.raise_for_status()
            b = bytearray()
            for c in r.iter_content(65536):
                b.extend(c)
                if len(b) > 5000000:
                    raise ValueError('unexpected archive size')
        z = zipfile.ZipFile(io.BytesIO(b))

    def load(name):
        info = z.getinfo(name)
        if info.file_size > 10000000:
            raise ValueError('unexpected member size')
        with io.TextIOWrapper(z.open(info), encoding='utf-8-sig', newline='') as f:
            return list(csv.DictReader(f))
    try:
        countries = load('CL_FI_COUNTRY_GROUPS.csv')
        matched = [x for x in countries if x['ISO3_Code'] == country]
        if len(matched) != 1:
            raise ValueError('country not found or ambiguous')
        code = matched[0]['UN_Code']
        maps = {}
        for dim, file in [('workarea', 'CL_FI_WORK_AREA.csv'), ('occupation', 'CL_FI_OCCUPATION.csv'), ('gender', 'CL_FI_GENDER.csv')]:
            maps[dim] = {x['Code']: x['Name_En'] for x in load(file)}
        flags = {x['Symbol']: x['Name_En'] for x in load('CL_FI_SYMBOL_SDMX.csv')}
        out = []
        count = 0
        for x in load('EMPLOY_NUMBER.csv'):
            y = x['PERIOD']
            if x['COUNTRY.UN_CODE'] != code or not y.isdigit() or (not start <= int(y) <= end):
                continue
            if workarea and x['WORKAREA.CODE'] != workarea or (occupation and x['OCCUPATION.CODE'] != occupation) or (gender and x['GENDER.CODE'] != gender):
                continue
            count += 1
            if count > offset and len(out) < limit:
                out.append({**x, 'workarea_label': maps['workarea'].get(x['WORKAREA.CODE']), 'occupation_label': maps['occupation'].get(x['OCCUPATION.CODE']), 'gender_label': maps['gender'].get(x['GENDER.CODE']), 'status_label': flags.get(x['STATUS'])})
        return {'provider': None if local_file else 'Food and Agriculture Organization of the United Nations', 'source': local_file if local_file else URL, 'documentation': INFO, 'edition': None if local_file else 'FishStat Global employment 2026.1.0', 'country': country, 'country_name': matched[0]['Name_En'], 'matched_count': count, 'offset': offset, 'limit': limit, 'next_offset': offset + limit if offset + limit < count else None, 'records': out, 'note': 'Archive is re-read each time; pin local_file to retain one version, as order may change across editions. Preserves work area, working time, sex and official/imputed status. Gender U means unknown, not a gender total. Categories and reported coverage may overlap; do not sum indiscriminately. MEASURE Q_no_1 is persons; consult accompanying metadata and country notes.' + (' Local archive provenance and version are unverified.' if local_file else '')}
    finally:
        z.close()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('country')
    p.add_argument('start', type=int)
    p.add_argument('end', type=int)
    p.add_argument('--workarea', default='')
    p.add_argument('--occupation', default='')
    p.add_argument('--gender', default='')
    p.add_argument('--limit', type=int, default=100)
    p.add_argument('--local-file')
    a = p.parse_args()
    print(json.dumps(query(a.country, a.start, a.end, a.workarea, a.occupation, a.gender, a.limit, a.local_file), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
