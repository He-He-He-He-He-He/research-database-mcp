"""Bank of Japan official public time-series API."""
import release_runtime
import re
import requests
BASE = 'https://www.stat-search.boj.or.jp/api/v1/'
MANUAL = 'https://www.stat-search.boj.or.jp/info/api_manual_en.pdf'
NOTICE = 'https://www.stat-search.boj.or.jp/info/api_notice_en.pdf'
NOTES = ['This uses the API provided by the Bank of Japan Time-Series Data Search. The Bank of Japan does not guarantee the content of this service.', 'The API launched in February 2026; current values may be revised and do not constitute a historical publication snapshot.', 'Preserve source frequency, units, dates, nulls and status. A call rate is not automatically the policy target rate.', 'NEXTPOSITION indicates partial output; request the next position before treating a result as complete. Avoid excessive request frequency. If releasing an API-based service, consult BOJ notice on notification and credit.']

def _token(v, name):
    if not isinstance(v, str) or not re.fullmatch('[A-Za-z0-9_]{1,50}', v):
        raise ValueError('Invalid ' + name)
    return v.upper()

def _get(path, params):
    r = requests.get(BASE + path, params={'format': 'json', 'lang': 'en', **params}, headers={'Accept-Encoding': 'gzip'}, timeout=60)
    r.raise_for_status()
    j = r.json()
    if not isinstance(j, dict) or j.get('STATUS') != 200 or (not isinstance(j.get('RESULTSET'), list)):
        raise ValueError('BOJ API did not return a successful result: ' + str(j.get('MESSAGE', 'unexpected response')) if isinstance(j, dict) else 'Unexpected BOJ response')
    return j

def metadata(db, keyword='', limit=20, offset=0):
    db = _token(db, 'database')
    if not isinstance(keyword, str) or len(keyword) > 100 or type(limit) is not int or (not 1 <= limit <= 100) or (type(offset) is not int) or (offset < 0):
        raise ValueError('Invalid metadata filter')
    j = _get('getMetadata', {'db': db})
    term = keyword.casefold()
    rows = [r for r in j['RESULTSET'] if r.get('SERIES_CODE') and term in (str(r.get('SERIES_CODE') or '') + ' ' + str(r.get('NAME_OF_TIME_SERIES') or '')).casefold()]
    return {'source': BASE + 'getMetadata', 'api_date': j.get('DATE'), 'database': db, 'total_matching': len(rows), 'offset': offset, 'notes': NOTES, 'records': rows[offset:offset + limit]}

def data(db, code, start, end, start_position=None):
    db = _token(db, 'database')
    code = _token(code, 'series code')
    if not all((isinstance(v, str) and re.fullmatch('\\d{4}(?:0[1-9]|1[0-2])?', v) for v in (start, end))) or len(start) != len(end) or start > end:
        raise ValueError('Dates must both be YYYY or YYYYMM and in order')
    p = {'db': db, 'code': code, 'startDate': start, 'endDate': end}
    if start_position is not None:
        if type(start_position) is not int or start_position < 1:
            raise ValueError('Invalid start position')
        p['startPosition'] = start_position
    j = _get('getDataCode', p)
    if any((r.get('SERIES_CODE') != code for r in j['RESULTSET'])):
        raise ValueError('BOJ returned an unexpected series')
    for r in j['RESULTSET']:
        vals = r.get('VALUES', {})
        if not isinstance(vals, dict) or not isinstance(vals.get('SURVEY_DATES'), list) or (not isinstance(vals.get('VALUES'), list)) or (len(vals['SURVEY_DATES']) != len(vals['VALUES'])):
            raise ValueError('BOJ dates and values are inconsistent')
    return {'source': BASE + 'getDataCode', 'request': p, 'api_date': j.get('DATE'), 'next_position': j.get('NEXTPOSITION'), 'complete': j.get('NEXTPOSITION') is None, 'notes': NOTES, 'records': j['RESULTSET']}
