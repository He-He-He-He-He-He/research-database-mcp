"""Bounded Eurostat JSON-stat query across selected geographies and periods."""
import release_runtime
import json, re, subprocess
from urllib.parse import urlencode
BASE = 'https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/'

def query(dataset, geographies, start, end, filters=None):
    if not isinstance(dataset, str) or not re.fullmatch('[A-Za-z0-9_]{1,80}', dataset):
        raise ValueError('invalid dataset')
    if not isinstance(geographies, list) or not 1 <= len(geographies) <= 20 or any((not isinstance(x, str) or not re.fullmatch('[A-Za-z0-9_]{1,30}', x) for x in geographies)) or (len(set(geographies)) != len(geographies)):
        raise ValueError('provide 1–20 distinct geography codes')
    pat = '\\d{4}(?:-(?:0[1-9]|1[0-2]|Q[1-4]))?'
    if not isinstance(start, str) or not isinstance(end, str) or (not re.fullmatch(pat, start)) or (not re.fullmatch(pat, end)) or (len(start) != len(end)) or (start > end):
        raise ValueError('invalid or inconsistent period range')
    if filters is None:
        filters = {}
    if not isinstance(filters, dict) or len(filters) > 12:
        raise ValueError('invalid filters')
    pairs = [('geo', x) for x in geographies] + [('sinceTimePeriod', start), ('untilTimePeriod', end), ('lang', 'en')]
    for k, v in filters.items():
        if not isinstance(k, str) or not re.fullmatch('[A-Za-z][A-Za-z0-9_]{0,40}', k) or k.lower() in {'geo', 'time', 'lang', 'sincetimeperiod', 'untiltimeperiod'}:
            raise ValueError('invalid or reserved dimension')
        vals = v if isinstance(v, list) else [v]
        if not 1 <= len(vals) <= 20 or any((not isinstance(x, str) or not re.fullmatch('[A-Za-z0-9_.-]{1,80}', x) for x in vals)) or len(set(vals)) != len(vals):
            raise ValueError('invalid dimension values')
        pairs.extend(((k, x) for x in vals))
    url = BASE + dataset + '?' + urlencode(pairs)
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', '--max-filesize', '10000000', url], capture_output=True, timeout=30)
    if p.returncode:
        raise RuntimeError('Eurostat request failed; narrow dimensions or check source status')
    if len(p.stdout) > 10000000:
        raise ValueError('response exceeds 10 MB; narrow dimensions')
    data = json.loads(p.stdout)
    if not isinstance(data, dict) or not isinstance(data.get('dimension'), dict) or (not isinstance(data.get('value'), (list, dict))) or (not isinstance(data.get('id'), list)) or (not isinstance(data.get('size'), list)) or (len(data['id']) != len(data['size'])):
        raise RuntimeError('unexpected JSON-stat response')
    for dim, requested in [('geo', geographies)] + [(k, v if isinstance(v, list) else [v]) for k, v in filters.items()]:
        entry = data['dimension'].get(dim)
        if not isinstance(entry, dict):
            raise RuntimeError('response omitted requested dimension ' + dim)
        idx = entry.get('category', {}).get('index')
        if not isinstance(idx, (dict, list)) or any((code not in requested for code in idx)):
            raise RuntimeError('response includes unrequested ' + dim + ' code')
    return {'source': 'Eurostat Statistics API', 'source_url': url, 'data': data, 'note': 'JSON-stat 的 id、size、dimension、value 和 status 必须一起解释；返回稀疏单元格，缺项不是零。区间可能包含缺失时间或地区；查看返回维度和状态，数据可修订。限制 10 MB。'}
