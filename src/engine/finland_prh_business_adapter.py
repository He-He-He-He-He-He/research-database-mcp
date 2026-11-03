"""Finland PRH/Tax Administration open YTJ business information API."""
import release_runtime
import json
import math
import re
import requests
URL = 'https://avoindata.prh.fi/opendata-ytj-api/v3/companies'
NOTES = ['Finnish Business Information System (YTJ/BIS) basic information is maintained by PRH and the Finnish Tax Administration; companies, foundations and other entities can appear.', 'Company name searches include previous, auxiliary and parallel names; a matching current name or active operating status is not guaranteed.', 'The public API provides basic information, not complete registers, owners, financial performance or operating permits. Fields may contain several names, registers and validity dates.', 'The source returns the first page if a requested page is out of range; this adapter rejects pages beyond the documented maximum inferred from totalResults and 100 results per page.', 'Current records may change and do not establish a historical snapshot. The official open API uses CC BY 4.0.']

def search(query, by='name', page=1):
    if not isinstance(query, str) or not query.strip() or len(query) > 100 or (by not in ('name', 'businessId')) or (type(page) is not int) or (not 1 <= page <= 10000):
        raise ValueError('Invalid query')
    if by == 'businessId' and (not re.fullmatch('\\d{7}-\\d', query)):
        raise ValueError('Business ID must be in 1234567-8 format')
    with requests.get(URL, params={by: query, 'page': page}, timeout=40, stream=True) as r:
        r.raise_for_status()
        raw = bytearray()
        for chunk in r.iter_content(65536):
            raw.extend(chunk)
            if len(raw) > 10000000:
                raise ValueError('response too large')
    j = json.loads(raw)
    if not isinstance(j, dict) or not isinstance(j.get('companies'), list) or type(j.get('totalResults')) is not int:
        raise ValueError('Unexpected PRH response')
    if page > max(1, math.ceil(j['totalResults'] / 100)):
        raise ValueError('Page exceeds total; PRH returns page one on out-of-range requests')
    return {'source': URL, 'query': query, 'search_by': by, 'requested_page': page, 'notes': NOTES, 'response': j}
