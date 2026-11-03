"""NIST NVD CVE API 2.0; one bounded request per query."""
import release_runtime
import json, re
import requests
URL = 'https://services.nvd.nist.gov/rest/json/cves/2.0'
DOC = 'https://nvd.nist.gov/developers/vulnerabilities'

def search(cve='', keyword='', limit=20, offset=0):
    if not isinstance(cve, str) or (cve and (not re.fullmatch('CVE-\\d{4}-\\d{4,}', cve))) or (not isinstance(keyword, str)) or (len(keyword) > 200) or (cve and keyword) or (not cve and (not keyword.strip())):
        raise ValueError('Provide one valid CVE or keyword')
    if type(limit) is not int or not 1 <= limit <= 100 or type(offset) is not int or (not 0 <= offset <= 1000000) or (cve and offset):
        raise ValueError('Invalid pagination')
    params = {'cveId': cve} if cve else {'keywordSearch': keyword.strip(), 'resultsPerPage': limit, 'startIndex': offset}
    with requests.get(URL, params=params, timeout=30, stream=True) as r:
        r.raise_for_status()
        raw = bytearray()
        for c in r.iter_content(65536):
            raw.extend(c)
            if len(raw) > 8000000:
                raise ValueError('Response exceeds size limit; reduce page size')
        source = r.url
    j = json.loads(raw)
    if j.get('format') != 'NVD_CVE' or not isinstance(j.get('vulnerabilities'), list):
        raise ValueError('Unexpected NVD response')
    return {'source': source, 'documentation': DOC, 'format': j['format'], 'api_version': j.get('version'), 'timestamp': j.get('timestamp'), 'total_results': j.get('totalResults'), 'start_index': j.get('startIndex'), 'results_per_page': j.get('resultsPerPage'), 'returned': len(j['vulnerabilities']), 'vulnerabilities': j['vulnerabilities'], 'notes': ['CVE descriptions, CVSS metrics, affected configurations and references are source records; assess applicability to the exact product and version.', 'CVSS severity is not the probability of exploitation. NVD CVE inclusion is not proof of exploitation; CISA KEV is a different catalog.', 'Current records can be revised; published and lastModified timestamps are distinct. One page is returned, not necessarily all matches.', 'Unauthenticated NVD requests are rate limited; this adapter does not silently retry or infer that an error means no results.']}
