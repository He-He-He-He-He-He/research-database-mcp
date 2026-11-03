"""国家天文科学数据中心公开数据资源检索及元数据详情。"""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
BASE = 'https://nadc.china-vo.org'

def _get(path, params=None):
    r = requests.get(BASE + path, params=params, timeout=20, allow_redirects=False)
    if r.status_code != 200:
        raise RuntimeError('上游 HTTP ' + str(r.status_code))
    r.encoding = 'utf-8'
    return r.text

def nadc_metadata_search(keyword):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100:
        raise ValueError('请输入关键词')
    html = _get('/essearch', {'keyword': keyword, 'endpoint': 'metadata', 'fuzziness': 1})
    s = BeautifulSoup(html, 'html.parser')
    out = []
    seen = set()
    for a in s.select('a[href]'):
        q = urlparse(urljoin(BASE, a['href']))
        m = re.fullmatch('/res/r(\\d+)/?', q.path)
        title = a.get_text(' ', strip=True)
        if q.scheme == 'https' and q.hostname == 'nadc.china-vo.org' and m and title and (m[1] not in seen):
            seen.add(m[1])
            out.append({'id': m[1], 'title': title, 'url': BASE + '/res/r' + m[1] + '/'})
    return {'items': out, 'note': '公开搜索结果当前页；仅保留数据资源条目。'}

def nadc_metadata_detail(identifier):
    if not re.fullmatch('\\d{1,12}', str(identifier)):
        raise ValueError('请输入资源编号')
    s = BeautifulSoup(_get('/res/r' + str(identifier) + '/'), 'html.parser')
    fields = {}
    for key in ('title', 'title_en', 'description', 'keywords', 'data_amount', 'formats', 'sharemode', 'sharescope', 'procedure'):
        e = s.find(id=key)
        if e:
            fields[key] = e.get_text(' ', strip=True)
    if not fields.get('title') or not fields.get('description'):
        raise ValueError('未识别数据资源详情')
    return {'id': str(identifier), 'url': BASE + '/res/r' + str(identifier) + '/', **fields, 'note': '元数据公开不保证文件开放；实际访问按资源说明及原站许可。'}
