"""OpenAIRE public research-project search API."""
import release_runtime
import json, re
import requests
URL = 'https://api.openaire.eu/search/projects'

def search(name, page=1, size=10, funder=None, country=None):
    if not isinstance(name, str) or not 1 <= len(name.strip()) <= 150:
        raise ValueError('Project name search must contain 1–150 characters')
    if any((isinstance(v, bool) or not isinstance(v, int) for v in (page, size))) or page < 1 or (not 1 <= size <= 50):
        raise ValueError('Invalid page or size')
    if funder is not None and funder not in ('EC', 'WT', 'ARC', 'ANDS', 'NSF', 'FCT', 'NHMRC'):
        raise ValueError('Unsupported funder')
    if country is not None and (not isinstance(country, str) or not re.fullmatch('[A-Z]{2}', country)):
        raise ValueError('Use an uppercase two-letter country code')
    p = {'name': name, 'page': page, 'size': size, 'format': 'json'}
    if funder:
        p['funder'] = funder
    if country:
        p['participantCountries'] = country
    with requests.get(URL, params=p, timeout=35, stream=True, allow_redirects=False) as r:
        if r.is_redirect or not r.ok:
            raise RuntimeError('OpenAIRE API returned HTTP ' + str(r.status_code))
        raw = bytearray()
        for c in r.iter_content(65536):
            raw.extend(c)
            if len(raw) > 8000000:
                raise RuntimeError('OpenAIRE response exceeds 8 MB')
    data = json.loads(raw)
    if not isinstance(data, dict) or not isinstance(data.get('response'), dict) or (not isinstance(data['response'].get('header'), dict)):
        raise RuntimeError('Unexpected OpenAIRE response')
    return {'source': 'OpenAIRE Graph Search API research projects', 'source_info': 'https://graph.openaire.eu/docs/10.8.1/apis/search-api/projects/', 'selection': {'name': name, 'page': page, 'size': size, 'funder': funder, 'participant_country': country}, 'response': data['response'], 'note': '公开研究项目索引来源可能包括资助机构及其他聚合来源；保留原始基金、项目金额、参与者和状态，须核原资助机构记录。单页不是全部项目，部分项目可能重复或已结束，金额不一定是已拨款。索引收录不等于浙大馆藏授权。'}
