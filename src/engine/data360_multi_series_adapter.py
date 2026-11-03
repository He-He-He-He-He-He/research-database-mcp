"""World Bank Data360 multi-country, multi-dimension observations."""
import release_runtime
import json, re, subprocess
from urllib.parse import urlencode
BASE = 'https://data360api.worldbank.org/data360/data'

def query(dataset, indicator, countries, start, end, filters=None):

    def token(s):
        return isinstance(s, str) and re.fullmatch('[A-Za-z0-9_.-]{1,100}', s)
    if not token(dataset) or not token(indicator):
        raise ValueError('invalid dataset or indicator')
    if not isinstance(countries, list) or not 1 <= len(countries) <= 20 or any((not isinstance(c, str) or not re.fullmatch('[A-Z]{3}', c) for c in countries)) or (len(set(countries)) != len(countries)):
        raise ValueError('provide 1–20 distinct uppercase area codes')
    if any((type(y) is not int for y in (start, end))) or not 1900 <= start <= end <= 2100:
        raise ValueError('invalid year range')
    if filters is None:
        filters = {}
    if not isinstance(filters, dict) or len(filters) > 12:
        raise ValueError('invalid filters')
    params = {'DATABASE_ID': dataset, 'INDICATOR': indicator, 'REF_AREA': ','.join(countries), 'timePeriodFrom': start, 'timePeriodTo': end}
    validated = {}
    for key, value in filters.items():
        if not isinstance(key, str) or not re.fullmatch('[A-Z][A-Z0-9_]{0,40}', key) or key in {'DATABASE_ID', 'INDICATOR', 'REF_AREA'}:
            raise ValueError('invalid or reserved dimension')
        vals = value if isinstance(value, list) else [value]
        if not 1 <= len(vals) <= 20 or any((not token(v) for v in vals)) or len(set(vals)) != len(vals):
            raise ValueError('invalid dimension values')
        validated[key] = vals
        params[key] = ','.join(vals)
    url = BASE + '?' + urlencode(params)
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', '--max-filesize', '10000000', url], capture_output=True, timeout=30)
    if p.returncode:
        raise RuntimeError('Data360 request failed; verify filters, network or source status')
    if len(p.stdout) > 10000000:
        raise ValueError('response exceeds 10 MB; narrow filters')
    j = json.loads(p.stdout)
    rows = j.get('value') if isinstance(j, dict) else None
    if not isinstance(rows, list) or type(j.get('count')) is not int or j['count'] != len(rows):
        raise RuntimeError('unexpected or inconsistent Data360 response')
    if any((not isinstance(r, dict) or r.get('DATABASE_ID') != dataset or r.get('INDICATOR') != indicator or (r.get('REF_AREA') not in countries) or any((r.get(k) not in v for k, v in validated.items())) for r in rows)):
        raise RuntimeError('Data360 response does not match requested dimensions')
    if any((not re.match('^\\d{4}', str(r.get('TIME_PERIOD', ''))) or not start <= int(str(r['TIME_PERIOD'])[:4]) <= end for r in rows)):
        raise RuntimeError('Data360 response does not match requested years')
    return {'source': 'World Bank Data360 API', 'source_url': url, 'metadata_url': f'https://data360files.worldbank.org/data360-data/metadata/{dataset}/{indicator}.pdf', 'count': len(rows), 'data': rows, 'note': '保留所有原始维度、状态、单位及 UNIT_MULT；不同单位、频率、人口分组不得混合。空结果不等于零。来源 count 与本次返回行数一致不证明大范围查询无上游截断；请缩小范围并核对来源，元数据链接不保证可用。'}
