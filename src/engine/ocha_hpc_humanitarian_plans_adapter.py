"""UN OCHA HPC public humanitarian plans and financial requirements by year."""
import release_runtime
import argparse, json, requests
URL = 'https://api.hpc.tools/v2/public/plan'
DOCS = 'https://github.com/un-ocha/hpc-api/wiki/Getting-All-Plans-for-a-Given-Year'

def query(year, keyword='', focus_location_id=None, limit=100):
    if isinstance(year, bool) or not isinstance(year, int) or (not 2000 <= year <= 2100) or isinstance(limit, bool) or (not isinstance(limit, int)) or (not 1 <= limit <= 200):
        raise ValueError('invalid year or limit')
    if not isinstance(keyword, str) or len(keyword) > 150 or (focus_location_id is not None and (isinstance(focus_location_id, bool) or not isinstance(focus_location_id, int) or focus_location_id < 1)):
        raise ValueError('invalid filter')
    r = requests.get(URL, params={'year': year}, timeout=40)
    r.raise_for_status()
    if len(r.content) > 10000000:
        raise ValueError('response exceeds size limit')
    j = r.json()
    data = j.get('data')
    if not isinstance(data, list):
        raise ValueError('unexpected API result')
    out = []
    count = 0
    for plan in data:
        p = plan.get('planVersion') or {}
        if not plan.get('isReleased') or keyword.casefold() not in str(p.get('name') or '').casefold() or (focus_location_id is not None and p.get('focusLocationId') != focus_location_id):
            continue
        count += 1
        if len(out) < limit:
            out.append({'id': plan.get('id'), 'name': p.get('name'), 'short_name': p.get('shortName'), 'type': p.get('subtitle'), 'start_date': p.get('startDate'), 'end_date': p.get('endDate'), 'focus_location_id': p.get('focusLocationId'), 'plan_code': p.get('code'), 'locations': plan.get('locations'), 'year_labels': plan.get('years'), 'original_requirements': plan.get('origRequirements'), 'revised_requirements': plan.get('revisedRequirements'), 'updated_at': plan.get('updatedAt')})
    return {'provider': 'UN OCHA Humanitarian Programme Cycle', 'source': r.url, 'documentation': DOCS, 'year_filter': year, 'keyword': keyword, 'matched_count': count, 'records': out, 'unit': 'USD for financial requirements', 'note': 'Only plans marked released; year filters plan activity, not necessarily only single-year plans. Requirements are requested funding, not received funds; initial and revised amounts can change. Plans may overlap by geography and purpose and should not be blindly summed. Blank values remain null.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('year', type=int)
    p.add_argument('--keyword', default='')
    p.add_argument('--focus-location-id', type=int)
    p.add_argument('--limit', type=int, default=100)
    a = p.parse_args()
    print(json.dumps(query(a.year, a.keyword, a.focus_location_id, a.limit), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
