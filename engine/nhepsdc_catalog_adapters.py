"""国家高能物理科学数据中心公开数据资源检索及详情。"""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
BASE = 'https://www.nhepsdc.cn'
COMPONENT = re.compile('[A-Za-z0-9_-]{1,80}')

def _get(path, params=None):
    r = requests.get(BASE + path, params=params, timeout=20, allow_redirects=False)
    if r.status_code != 200:
        raise RuntimeError('上游 HTTP ' + str(r.status_code))
    return r

def nhepsdc_search(keyword, page=1, size=10):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100 or (not isinstance(page, int)) or (not 1 <= page <= 100) or (not isinstance(size, int)) or (not 1 <= size <= 50):
        raise ValueError('请检查关键词和分页')
    x = _get('/api/resource/dataset/page', {'search': keyword, 'page': page, 'size': size}).json()
    if x.get('status') != 0 or not isinstance(x.get('result'), list):
        raise ValueError('未识别公开数据目录')
    fields = ('dataTypeCode', 'dataCode', 'code', 'name', 'keywords', 'dataIdentifier', 'decription', 'lastModifiedDate', 'dataTotal')
    out = []
    for item in x['result']:
        if all((COMPONENT.fullmatch(str(item.get(k, ''))) for k in ('dataTypeCode', 'dataCode', 'code'))):
            out.append({k: item.get(k) for k in fields})
    return {'total': x.get('total'), 'page': page, 'items': out, 'note': '公开检索元数据；文件权限以数据详情为准。'}

def nhepsdc_detail(data_type, data_code, code):
    if any((not isinstance(x, str) or not COMPONENT.fullmatch(x) for x in (data_type, data_code, code))):
        raise ValueError('请输入数据资源路径编号')
    path = '/resource/' + data_type + '/' + data_code + '/' + code
    r = _get(path)
    r.encoding = 'utf-8'
    s = BeautifulSoup(r.text, 'html.parser')
    title = s.select_one('.detail-title')
    area = s.select_one('.detail-info')
    if not title or not area:
        raise ValueError('未识别资源详情')
    fields = {}
    for row in area.select('.info-row'):
        label = row.select_one('.info-label')
        children = row.find_all('div', recursive=False)
        if label and len(children) >= 2:
            name = label.get_text(' ', strip=True)
            if name in ('Keywords', 'CSTR', 'Source Institution', 'Abstract', 'Discipline Classification'):
                fields[name] = children[1].get_text(' ', strip=True)
    strategy = {}
    box = s.select_one('[data-tab="strategy"].meta-card')
    if box:
        for row in box.select('tr'):
            cols = row.find_all('td', recursive=False)
            if len(cols) == 2:
                strategy[cols[0].get_text(' ', strip=True)] = cols[1].get_text(' ', strip=True)
    return {'url': BASE + path, 'title': title.get_text(' ', strip=True), 'metadata': fields, 'access_strategy': strategy, 'note': '不下载数据文件；以原站访问策略、许可与版本为准。'}
