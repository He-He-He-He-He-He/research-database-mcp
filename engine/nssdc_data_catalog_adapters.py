"""国家空间科学数据中心数据访问系统公开目录与元数据。"""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs
BASE = 'https://dataaccess.nssdc.ac.cn'

def _get(path, params=None):
    r = requests.get(BASE + path, params=params, timeout=20, allow_redirects=False)
    if r.status_code != 200:
        raise RuntimeError('上游 HTTP ' + str(r.status_code))
    r.encoding = 'utf-8'
    return r.text

def nssdc_catalog(keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('请输入不超过 100 字的关键词')
    s = BeautifulSoup(_get('/dataSet/rcview'), 'html.parser')
    seen = set()
    out = []
    for a in s.select('a[href]'):
        u = urlparse(urljoin(BASE, a['href']))
        ids = parse_qs(u.query).get('dsId', [])
        title = a.get_text(' ', strip=True)
        if u.scheme == 'https' and u.hostname == 'dataaccess.nssdc.ac.cn' and (u.path == '/dataSet/view') and (len(ids) == 1) and re.fullmatch('\\d{1,10}', ids[0]) and (ids[0] not in seen) and (keyword in title):
            seen.add(ids[0])
            out.append({'id': ids[0], 'title': title})
    if not out and (not keyword):
        raise ValueError('未识别公开目录')
    return out

def nssdc_dataset_detail(identifier):
    if not re.fullmatch('\\d{1,10}', str(identifier)):
        raise ValueError('请输入数据集数字编号')
    s = BeautifulSoup(_get('/dataSet/view', {'dsId': identifier}), 'html.parser')
    area = s.select_one('.content_div')
    if area is None:
        raise ValueError('未识别数据集详情')
    title = area.select_one('h3')
    desc = next((d for d in area.find_all('div', style=True) if 'width: 80%' in d['style']), None)
    if not title or not desc:
        raise ValueError('未识别数据集标题或描述')
    keys = {'观测区域', '观测对象', '物理参数', '观测网络', '观测平台', '观测仪器'}
    meta = {}
    for row in area.select('table tr'):
        cells = [x.get_text(' ', strip=True) for x in row.find_all('td', recursive=False)]
        for i in range(0, len(cells) - 1, 2):
            if cells[i] in keys:
                meta[cells[i]] = cells[i + 1]
    return {'id': str(identifier), 'title': title.get_text(' ', strip=True), 'description': desc.get_text(' ', strip=True), 'metadata': meta, 'url': BASE + '/dataSet/view?dsId=' + str(identifier), 'note': '公开目录与元数据；文件获取权限以原平台为准。'}
