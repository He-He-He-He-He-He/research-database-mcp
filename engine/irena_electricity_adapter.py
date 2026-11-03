"""IRENA 官方 IRENASTAT PxWeb 2026 H2 发电及装机统计。"""
import release_runtime
import requests
URL = 'https://pxweb.irena.org/api/v1/en/IRENASTAT/Power%20Capacity%20and%20Generation/Country_ELECSTAT_2026_H2_PX.px'

def electricity(country, technology='1', data_type='1', grid='0', start=2020, end=2025):
    if not isinstance(country, str) or not country.isalpha() or (not 3 <= len(country) <= 4) or (country != country.upper()):
        raise ValueError('country 应为 IRENA 的地区代码，例如 CHN')
    if data_type not in {'0', '1'} or grid not in {'0', '1', '2'}:
        raise ValueError('数据类型或电网连接代码无效')
    if not isinstance(technology, str) or not technology.isdecimal():
        raise ValueError('technology 应为 IRENA 技术代码')
    if any((isinstance(v, bool) or not isinstance(v, int) or (not 2000 <= v <= 2025) for v in (start, end))) or start > end:
        raise ValueError('本版年份范围为 2000 至 2025，开始不得晚于结束')
    session = requests.Session()
    r = session.get(URL, timeout=25)
    r.raise_for_status()
    meta = r.json()
    variables = {v['code']: v for v in meta.get('variables', [])}
    wanted = ['Country/area', 'Technology', 'Data Type', 'Grid connection', 'Year']
    if set(wanted) - variables.keys():
        raise RuntimeError('IRENA 元数据维度发生变化')
    selected = {'Country/area': [country], 'Technology': [technology], 'Data Type': [data_type], 'Grid connection': [grid], 'Year': [code for code, label in zip(variables['Year']['values'], variables['Year']['valueTexts']) if label.isdigit() and start <= int(label) <= end]}
    for key in wanted:
        if not selected[key] or any((x not in variables[key]['values'] for x in selected[key])):
            raise ValueError(f'IRENA 不支持所选 {key}')
    payload = {'query': [{'code': k, 'selection': {'filter': 'item', 'values': selected[k]}} for k in wanted], 'response': {'format': 'json-stat2'}}
    r = session.post(URL, json=payload, timeout=30)
    r.raise_for_status()
    d = r.json()
    if d.get('id') != wanted or d.get('size') != [1, 1, 1, 1, len(selected['Year'])]:
        raise RuntimeError('IRENA 返回的数据维度不符')
    years = d['dimension']['Year']['category']
    index = years['index']
    labels = years['label']
    values = d.get('value', [])
    statuses = d.get('status', {})

    def at(data, i):
        if isinstance(data, list):
            return data[i] if i < len(data) else None
        return data.get(str(i)) if isinstance(data, dict) else None
    items = [{'year': int(labels[k]), 'value': at(values, i), 'status': at(statuses, i)} for k, i in index.items()]
    items.sort(key=lambda x: x['year'], reverse=True)
    getlabel = lambda key: d['dimension'][key]['category']['label'][selected[key][0]]
    return {'source': d.get('source'), 'country': country, 'country_label': getlabel('Country/area'), 'technology': technology, 'technology_label': getlabel('Technology'), 'data_type': getlabel('Data Type'), 'grid': getlabel('Grid connection'), 'items': items, 'scope': 'IRENA 2026 H2 版；装机容量为 MW、发电量为 GWh，具体以 data_type 为准。来源含官方统计和估算；保留空值与原始状态。', 'documentation': 'https://pxweb.irena.org/pxweb/en/IRENASTAT/IRENASTAT__Power%20Capacity%20and%20Generation/Country_ELECSTAT_2026_H2_PX.px/'}
