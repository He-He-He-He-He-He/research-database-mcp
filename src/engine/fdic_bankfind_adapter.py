"""FDIC BankFind public institutions and quarterly financial reports."""
import release_runtime
import datetime
import re
import requests
BASE = 'https://api.fdic.gov/banks/'
SOURCE = 'https://api.fdic.gov/banks/docs/'
NOTES = ['FDIC CERT identifies an institution; bank records are not bank holding company consolidated statements.', 'Financial amounts ASSET, DEP and NETINCQ are in thousands of US dollars; NETINCQ is quarterly net income.', 'REPDTE is the reporting date, not the date on which the information became available; use the index timestamp for the retrieved version.', 'Past records and institution status can be revised; ACTIVE reflects the returned directory field, not an assessment of current solvency.']

def _cert(value):
    s = str(value)
    if not re.fullmatch('[0-9]{1,9}', s) or int(s) < 1:
        raise ValueError('CERT must be a positive integer')
    return int(s)

def _date(value):
    s = str(value)
    if not re.fullmatch('\\d{8}', s):
        raise ValueError('date must be YYYYMMDD')
    datetime.datetime.strptime(s, '%Y%m%d')
    return s

def _fetch(endpoint, params, limit):
    response = requests.get(BASE + endpoint, params={**params, 'format': 'json'}, timeout=45)
    response.raise_for_status()
    body = response.json()
    if not isinstance(body, dict) or not isinstance(body.get('meta'), dict) or (not isinstance(body.get('data'), list)):
        raise ValueError('unexpected FDIC response')
    total = body['meta'].get('total')
    if not isinstance(total, int) or len(body['data']) > limit:
        raise ValueError('invalid FDIC pagination metadata')
    records = []
    for item in body['data']:
        if not isinstance(item, dict) or not isinstance(item.get('data'), dict):
            raise ValueError('invalid FDIC record')
        records.append(item['data'])
    return {'source': SOURCE, 'endpoint': BASE + endpoint, 'meta': body['meta'], 'notes': NOTES, 'records': records}

def institution(cert):
    cert = _cert(cert)
    result = _fetch('institutions', {'filters': f'CERT:{cert}', 'fields': 'CERT,NAME,CITY,STNAME,ACTIVE,ASSET,DEP,DATEUPDT', 'limit': 1}, 1)
    if any((str(row.get('CERT')) != str(cert) for row in result['records'])):
        raise ValueError('FDIC returned an unexpected institution')
    return result

def financials(cert, start, end, offset=0, limit=20):
    cert, start, end = (_cert(cert), _date(start), _date(end))
    if start > end:
        raise ValueError('start must not be after end')
    if type(offset) is not int or offset < 0 or type(limit) is not int or (not 1 <= limit <= 100):
        raise ValueError('offset must be nonnegative and limit must be between 1 and 100')
    result = _fetch('financials', {'filters': f'CERT:{cert} AND REPDTE:[{start} TO {end}]', 'fields': 'CERT,NAME,REPDTE,ASSET,DEP,NETINCQ', 'sort_by': 'REPDTE', 'sort_order': 'DESC', 'offset': offset, 'limit': limit}, limit)
    for row in result['records']:
        report_date = _date(row.get('REPDTE'))
        if str(row.get('CERT')) != str(cert) or not start <= report_date <= end:
            raise ValueError('FDIC returned a record outside the requested scope')
    return result
