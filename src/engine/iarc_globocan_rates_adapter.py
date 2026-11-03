"""IARC GLOBOCAN country all-ages estimates through Cancer Today service."""
import release_runtime
import requests
BASE = 'https://gco-api.iarc.fr/api/globocan/v3/'
TYPES = {'incidence': 0, 'mortality': 1}
SEX = {'both': 0, 'male': 1, 'female': 2}
CANCER = {'all': 39, 'lung': 15}

def query(population, year=2024, kind='incidence', sex='both', cancer='all'):
    if isinstance(population, bool) or not isinstance(population, int) or (not 1 <= population <= 999):
        raise ValueError('Population must be an IARC numeric code 1–999')
    if isinstance(year, bool) or year not in (2022, 2024):
        raise ValueError('Supported versions are 2022 and 2024')
    if kind not in TYPES or sex not in SEX or cancer not in CANCER:
        raise ValueError('Invalid indicator selection')
    url = f'{BASE}{year}/data/rate/{TYPES[kind]}/{SEX[sex]}/{population}/{CANCER[cancer]}/'
    with requests.get(url, timeout=30, stream=True, allow_redirects=False) as response:
        if response.is_redirect or not response.ok:
            raise RuntimeError('IARC service returned HTTP ' + str(response.status_code))
        body = bytearray()
        for part in response.iter_content(65536):
            body.extend(part)
            if len(body) > 1000000:
                raise RuntimeError('IARC response exceeds 1 MB')
    import json
    d = json.loads(body)
    if not isinstance(d, dict) or not isinstance(d.get('dataset'), list) or (not isinstance(d.get('error'), list)):
        raise RuntimeError('Unexpected IARC response')
    if d['error']:
        raise RuntimeError('IARC service reported an error')
    if any((not isinstance(x, dict) or x.get('country_code') != population or x.get('sex') != SEX[sex] or (x.get('type') != TYPES[kind]) or (x.get('cancer_code') != CANCER[cancer]) for x in d['dataset'])):
        raise RuntimeError('IARC response does not match query')
    return {'source': 'IARC Global Cancer Observatory GLOBOCAN', 'source_url': url, 'official_website': 'https://gco.iarc.who.int/today/', 'selection': {'version_year': year, 'population_code': population, 'kind': kind, 'sex': sex, 'cancer': cancer, 'age': 'all ages'}, 'response': d, 'note': '按发布版本的国家或地区估计，非逐例登记实数；每10万人年龄标准化率 asr 使用世界标准人口，粗率 crude_rate 未年龄标准化；cum_risk_74 为75岁前累积风险百分比。数据估计方法、覆盖及修订影响跨年比较，人口代码及癌种须核 IARC。空结果不代表零。摘录研究应署名 IARC；商业及大规模传播须核使用许可：https://www.iarc.who.int/copyright-notice/'}
