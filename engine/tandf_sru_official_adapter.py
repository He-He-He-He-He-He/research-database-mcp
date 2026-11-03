"""One-page official Taylor & Francis Online SRU catalogue search."""
import release_runtime
import re
import xml.etree.ElementTree as ET
import requests
URL = 'https://www.tandfonline.com/action/sru'

def search(keyword, page=1, page_size=5, timeout=20):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100 or re.search('["\\\\\\r\\n]', keyword):
        raise ValueError('keyword must be 1–100 characters without quotes or backslashes')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 100):
        raise ValueError('page must be from 1 to 100')
    if isinstance(page_size, bool) or not isinstance(page_size, int) or (not 1 <= page_size <= 20):
        raise ValueError('page_size must be from 1 to 20')
    r = requests.get(URL, params={'query': f'cql.anywhere="{keyword.strip()}"', 'maximumRecords': page_size, 'startRecord': (page - 1) * page_size + 1}, timeout=timeout)
    r.raise_for_status()
    try:
        root = ET.fromstring(r.content)
    except ET.ParseError as exc:
        raise ValueError('SRU did not return XML') from exc
    sr = '{http://docs.oasis-open.org/ns/search-ws/sruResponse}'
    dc = '{http://purl.org/dc/elements/1.1/}'
    dct = '{http://purl.org/dc/terms/}'
    prism = '{http://prismstandard.org/namespaces/basic/2.1/}'
    total = root.findtext(sr + 'numberOfRecords')
    if total is None or not total.isdecimal():
        raise ValueError('SRU response lacks result count')
    records = []
    for record in root.findall('.//' + sr + 'record'):
        data = record.find('.//' + dc + 'dc')
        if data is None:
            raise ValueError('SRU record lacks metadata')
        records.append({'title': data.findtext(dc + 'title'), 'doi': data.findtext(dc + 'identifier'), 'authors': [e.text for e in data.findall(dc + 'contributor')], 'publication': data.findtext(dct + 'isPartOf'), 'date': data.findtext(dc + 'date'), 'url': data.findtext(prism + 'url'), 'position': record.findtext(sr + 'recordPosition')})
    if len(records) > page_size:
        raise ValueError('unexpected record count')
    return {'source': 'Taylor & Francis Online official SRU', 'keyword': keyword.strip(), 'page': page, 'page_size': page_size, 'total': int(total), 'records': records, 'note': '出版社全平台题录，不证明浙江大学订购范围、全文权限或 AI 用途授权。'}
