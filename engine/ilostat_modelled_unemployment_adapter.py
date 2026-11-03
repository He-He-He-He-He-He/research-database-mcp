"""ILO modelled unemployment rate by sex and age; edition not verified by the data response."""
import release_runtime
import argparse, csv, io, json, re, requests
BASE = 'https://sdmx.ilo.org/rest/data/ILO,DF_UNE_2EAP_SEX_AGE_RT/'

def query(country, start, end, sex='SEX_T', age='AGE_YTHADULT_YGE15'):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country) or sex not in ('SEX_T', 'SEX_M', 'SEX_F') or (not isinstance(age, str)) or (not re.fullmatch('AGE_[A-Z0-9_-]{1,60}', age)) or (not 1990 <= start <= end <= 2100) or (end - start > 20):
        raise ValueError('invalid query')
    url = BASE + country + '.A..' + sex + '.' + age
    r = requests.get(url, params={'startPeriod': start, 'endPeriod': end, 'format': 'csv'}, timeout=45)
    r.raise_for_status()
    if r.status_code == 204:
        return {'source': r.url, 'records': []}
    if len(r.content) > 1000000:
        raise ValueError('unexpected response size')
    reader = csv.DictReader(io.StringIO(r.content.decode('utf-8-sig')))
    if not {'REF_AREA', 'SEX', 'AGE', 'OBS_VALUE', 'UNIT_MEASURE', 'UNIT_MULT', 'TIME_PERIOD', 'SOURCE'}.issubset(reader.fieldnames or []):
        raise ValueError('unexpected schema')
    rows = list(reader)
    if any((x['REF_AREA'] != country or x['SEX'] != sex or x['AGE'] != age or (x['UNIT_MEASURE'] != 'PT') or (x['UNIT_MULT'] != '0') or (not start <= int(x['TIME_PERIOD']) <= end) for x in rows)):
        raise ValueError('unexpected dimensions or units')
    return {'source': r.url, 'dataset': 'ILO modelled estimates', 'records': rows, 'note': 'Percent of labour force, not of total population. The source data response does not establish a model edition; check ILO metadata for the edition and whether individual values are estimates or forecasts. Model results may differ from national survey releases.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('country')
    p.add_argument('start', type=int)
    p.add_argument('end', type=int)
    p.add_argument('--sex', choices=['SEX_T', 'SEX_M', 'SEX_F'], default='SEX_T')
    p.add_argument('--age', default='AGE_YTHADULT_YGE15')
    a = p.parse_args()
    print(json.dumps(query(a.country, a.start, a.end, a.sex, a.age), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
