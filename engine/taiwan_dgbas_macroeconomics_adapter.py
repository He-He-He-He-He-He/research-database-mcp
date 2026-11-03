"""Search official Taiwan macroeconomic XML observation files."""
import release_runtime
import requests
import xml.etree.ElementTree as ET
BASE = 'https://ws.dgbas.gov.tw/001/Upload/461/relfile/11525/'
SOURCES = {'gdp_industry': ('230912/na8103a1a.xml', '产业生产、GDP及平减指数（年）', 'https://data.gov.tw/dataset/44222'), 'cpi_basic': ('230555/pr0101a1m.xml', '消费者物价基本分类指数（月）', 'https://data.gov.tw/dataset/6019'), 'gdp_quarter': ('230514/na8101a1q.xml', '国民所得常用资料（季）', 'https://data.gov.tw/dataset/6799'), 'cpi_special': ('230544/pr0103a1m.xml', '消费者物价特殊分类指数（月）', 'https://data.gov.tw/dataset/8237')}

def catalog():
    return [{'code': k, 'title': v[1], 'url': BASE + v[0], 'metadata_url': v[2]} for k, v in SOURCES.items()]

def query(dataset, item='', period='', value_type='', limit=100, offset=0):
    if dataset not in SOURCES:
        raise ValueError('未知数据集，请先查看目录')
    if not 1 <= int(limit) <= 1000 or int(offset) < 0:
        raise ValueError('limit 应为 1–1000，offset 不可为负')
    url = BASE + SOURCES[dataset][0]
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    root = ET.fromstring(r.content)
    if root.tag != 'DataSet':
        raise RuntimeError('来源返回非预期统计数据')
    records = []
    total = 0
    for node in root.findall('Obs'):
        row = {child.tag: child.text or '' for child in node}
        if item not in row.get('Item', '') or not row.get('TIME_PERIOD', '').startswith(period) or (value_type and row.get('TYPE') != value_type):
            continue
        if int(offset) <= total < int(offset) + int(limit):
            records.append(row)
        total += 1
    return {'dataset': dataset, 'title': SOURCES[dataset][1], 'url': url, 'metadata_url': SOURCES[dataset][2], 'count': total, 'offset': int(offset), 'records': records, 'note': '数据文件整体下载后本地筛选；原值、百分比和基期均以官方 Item 和 TYPE 为准。'}
