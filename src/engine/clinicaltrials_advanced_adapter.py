"""ClinicalTrials.gov v2 combined search; use existing detail endpoint for NCT IDs."""
import release_runtime
import datetime, re, requests
URL = 'https://clinicaltrials.gov/api/v2/studies'

def search(condition, intervention='', location='', statuses=None, first_posted=None, size=10, page_token=None):
    for x in (condition, intervention, location):
        if not isinstance(x, str) or len(x) > 200 or any((ord(c) < 32 for c in x)):
            raise ValueError('invalid query term')
    if not condition.strip() and (not intervention.strip()) and (not location.strip()):
        raise ValueError('provide a condition, intervention, or location')
    statuses = [] if statuses is None else statuses
    if not isinstance(statuses, list) or len(statuses) > 15 or len(set(statuses)) != len(statuses) or any((not isinstance(s, str) or not re.fullmatch('[A-Z_]{3,40}', s) for s in statuses)):
        raise ValueError('invalid statuses')
    if type(size) is not int or not 1 <= size <= 20 or (page_token is not None and (not isinstance(page_token, str) or len(page_token) > 2000 or any((ord(c) < 32 for c in page_token)))):
        raise ValueError('invalid size or page token')
    if first_posted is not None:
        if not isinstance(first_posted, (list, tuple)) or len(first_posted) != 2:
            raise ValueError('date range requires start/end')
        for d in first_posted:
            if not isinstance(d, str) or not re.fullmatch('\\d{4}-\\d{2}-\\d{2}', d):
                raise ValueError('date must be YYYY-MM-DD')
            try:
                datetime.date.fromisoformat(d)
            except ValueError:
                raise ValueError('invalid date') from None
        if first_posted[0] > first_posted[1]:
            raise ValueError('date range reversed')
    p = {'pageSize': size, 'countTotal': 'true', 'format': 'json'}
    if condition.strip():
        p['query.cond'] = condition.strip()
    if intervention.strip():
        p['query.intr'] = intervention.strip()
    if location.strip():
        p['query.locn'] = location.strip()
    if statuses:
        p['filter.overallStatus'] = ','.join(statuses)
    if first_posted:
        p['filter.advanced'] = 'AREA[StudyFirstPostDate]RANGE[' + ','.join(first_posted) + ']'
    if page_token:
        p['pageToken'] = page_token
    with requests.get(URL, params=p, timeout=(10, 25), stream=True, allow_redirects=False) as r:
        r.raise_for_status()
        source = r.url
        body = bytearray()
        for b in r.iter_content(65536):
            body.extend(b)
            if len(body) > 10000000:
                raise ValueError('response exceeds 10 MB; reduce page size')
    import json
    try:
        j = json.loads(body)
    except ValueError:
        raise RuntimeError('ClinicalTrials.gov returned non-JSON') from None
    rows = j.get('studies') if isinstance(j, dict) else None
    total = j.get('totalCount') if isinstance(j, dict) else None
    if not isinstance(rows, list) or len(rows) > size or type(total) is not int or (total < 0):
        raise RuntimeError('unexpected study search response')
    unknown = []
    for x in rows:
        protocol = x.get('protocolSection', {})
        id = protocol.get('identificationModule', {}).get('nctId')
        status = protocol.get('statusModule', {})
        if not isinstance(id, str) or not re.fullmatch('NCT\\d{8}', id):
            raise RuntimeError('study missing valid NCT ID')
        if statuses and status.get('overallStatus') not in statuses:
            raise RuntimeError('returned study outside requested status')
        if first_posted:
            date = (status.get('studyFirstPostDateStruct') or {}).get('date')
            if not isinstance(date, str) or not re.fullmatch('\\d{4}-\\d{2}-\\d{2}', date):
                unknown.append(id)
            elif not first_posted[0] <= date <= first_posted[1]:
                raise RuntimeError('returned study outside requested first-posted dates')
    return {'source_url': source, 'query': p, 'total': total, 'returned': len(rows), 'next_page_token': j.get('nextPageToken'), 'studies': rows, 'date_not_verified_ids': unknown, 'note': '地点为官方搜索字段匹配，不保证是精确国家或全部研究地点；首次发布日期不是开始日期，招募状态及资格可能变化。注册研究不等于疗效或安全性已证实；具体项目请查 NCT 详情。跨页结果可能变动。'}
