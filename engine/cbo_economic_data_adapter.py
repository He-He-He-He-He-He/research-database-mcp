"""CBO official machine-readable historical economic data and projections."""
import release_runtime
import csv
import hashlib
import io
import json
import re
import requests
BASE = 'https://raw.githubusercontent.com/US-CBO/cbo-data/main/'
CATALOG = 'catalog.json'
DATASET = 'historical_economic'
MAX_BYTES = 5000000

def _get(path):
    if not re.fullmatch('[a-zA-Z0-9_./-]+', path) or '..' in path or path.startswith('/'):
        raise ValueError('Invalid repository path')
    with requests.get(BASE + path, timeout=40, stream=True, allow_redirects=False) as response:
        if response.is_redirect or not response.ok:
            raise RuntimeError('CBO repository request failed: HTTP ' + str(response.status_code))
        data = bytearray()
        for part in response.iter_content(65536):
            data.extend(part)
            if len(data) > MAX_BYTES:
                raise RuntimeError('CBO file exceeds 5 MB')
    return bytes(data)

def catalog():
    data = json.loads(_get(CATALOG))
    matches = [d for d in data['datasets'] if d.get('identifier') == DATASET]
    if len(matches) != 1:
        raise RuntimeError('CBO catalogue dataset missing or ambiguous')
    return {'source': 'US Congressional Budget Office open-data repository', 'source_info': 'https://www.cbo.gov/data/budget-economic-data', 'catalog_generated': data.get('generated'), 'dataset': matches[0], 'note': '每个文件是特定发布版本；当前目录和数据可能更新。'}

def fields():
    c = catalog()
    path = c['dataset']['schema_path']
    s = json.loads(_get(path))
    if s.get('dataset') != DATASET or not isinstance(s.get('fields'), dict):
        raise RuntimeError('Unexpected CBO schema')
    return {'source': BASE + path, 'catalog_generated': c['catalog_generated'], 'schema': s, 'note': '列单位、频率及聚合规则以字段定义为准；历史值可能修订。'}

def query(variable, vintage, frequency, start_year, end_year):
    if not isinstance(variable, str) or not re.fullmatch('[a-z][a-z0-9_]{0,100}', variable):
        raise ValueError('Invalid variable')
    if not isinstance(vintage, str) or not re.fullmatch('\\d{4}-(?:0[1-9]|1[0-2])', vintage):
        raise ValueError('Invalid vintage')
    if frequency not in ('quarterly', 'annual_cy', 'annual_fy'):
        raise ValueError('Invalid frequency')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start_year, end_year))) or not 1900 <= start_year <= end_year <= 2200:
        raise ValueError('Invalid year range')
    c = catalog()
    d = c['dataset']
    schema = json.loads(_get(d['schema_path']))
    if schema.get('dataset') != DATASET or variable not in schema.get('fields', {}):
        raise ValueError('Variable absent from current schema')
    dist = [x for x in d['distribution'] if x.get('vintage') == vintage and x.get('file_type') == frequency]
    if len(dist) != 1:
        raise ValueError('Vintage and frequency not available in official catalog')
    path = dist[0]['downloadURL']
    expected = f'data/economic/historical_economic/{frequency}_{vintage}.csv'
    if path != expected:
        raise RuntimeError('Unexpected CBO catalog path')
    content = _get(path)
    reader = csv.DictReader(io.StringIO(content.decode('utf-8-sig')))
    if reader.fieldnames is None or not {'date', 'variable', 'value'}.issubset(reader.fieldnames):
        raise RuntimeError('Unexpected CBO CSV schema')
    rows = []
    for row in reader:
        if row.get('variable') != variable:
            continue
        date = row.get('date', '')
        m = re.fullmatch('(?:FY|CY)?(\\d{4})(?:q[1-4])?', date)
        if not m:
            raise RuntimeError('Unexpected CBO date')
        if start_year <= int(m.group(1)) <= end_year:
            rows.append(row)
    return {'source': 'US CBO historical economic and projection dataset via official GitHub repository', 'source_url': BASE + path, 'official_publication': d.get('landingPage'), 'vintage': vintage, 'frequency': frequency, 'variable': variable, 'variable_metadata': schema['fields'][variable], 'file_bytes': len(content), 'sha256': hashlib.sha256(content).hexdigest(), 'returned': len(rows), 'items': rows, 'note': '历史值和预测可能同时存在；上游未标记时不能仅凭年份判断为实际或预测，应核该版本原报告。CY 为日历年，FY 为财政年；保留原字符串和所有标记。空结果不代表零；文件为 CBO 公开 GitHub 机器整理版，原 CBO 页面为权威来源。'}
