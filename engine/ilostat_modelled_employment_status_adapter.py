"""ILO modelled employment by sex and status in employment; edition not established by the data response."""
import release_runtime
import argparse, csv, io, json, re, requests
BASE = 'https://sdmx.ilo.org/rest/data/ILO,DF_EMP_2EMP_SEX_STE_NB/'

def query(country, start, end, sex='SEX_T'):
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country) or sex not in ('SEX_T', 'SEX_M', 'SEX_F') or (not 1990 <= start <= end <= 2100) or (end - start > 20):
        raise ValueError('invalid query')
    url = BASE + country + '.A..' + sex + '.'
    r = requests.get(url, params={'startPeriod': start, 'endPeriod': end, 'format': 'csv'}, timeout=45)
    r.raise_for_status()
    if r.status_code == 204:
        return {'source': r.url, 'records': []}
    if len(r.content) > 5000000:
        raise ValueError('unexpected response size')
    reader = csv.DictReader(io.StringIO(r.content.decode('utf-8-sig')))
    if not {'REF_AREA', 'SEX', 'STE', 'OBS_VALUE', 'UNIT_MEASURE', 'UNIT_MULT', 'TIME_PERIOD', 'SOURCE'}.issubset(reader.fieldnames or []):
        raise ValueError('unexpected CSV response')
    rows = list(reader)
    if any((x['REF_AREA'] != country or x['SEX'] != sex or (not start <= int(x['TIME_PERIOD']) <= end) for x in rows)):
        raise ValueError('unexpected dimensions')
    return {'source': r.url, 'dataset': 'ILO modelled estimates', 'records': rows, 'note': 'Raw OBS_VALUE times 10^UNIT_MULT persons; status classifications may overlap and should not be summed blindly. Values are modelled estimates/projections; the source response does not establish the model edition. Check ILO metadata for the edition and observation status.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('country')
    p.add_argument('start', type=int)
    p.add_argument('end', type=int)
    p.add_argument('--sex', choices=['SEX_T', 'SEX_M', 'SEX_F'], default='SEX_T')
    a = p.parse_args()
    print(json.dumps(query(a.country, a.start, a.end, a.sex), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
