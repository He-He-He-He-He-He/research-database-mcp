"""北京大学文科数智化平台国内高校与研究机构公开数据库导航。"""
import release_runtime
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
BASE = 'https://hdipp.pku.edu.cn/sjzy/sjk/gksjk/gngx_yjjgsjk.htm'

def survey_directory(keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('关键词不超过 100 字')
    r = requests.get(BASE, timeout=20, allow_redirects=False)
    if r.status_code != 200:
        raise RuntimeError('上游 HTTP ' + str(r.status_code))
    r.encoding = 'utf-8'
    s = BeautifulSoup(r.text, 'html.parser')
    items = []
    for a in s.select('ul.sjk_gj_ul > li > a[href]'):
        title = a.get('title') or a.get_text(' ', strip=True)
        url = urljoin(BASE, a['href'])
        p = urlparse(url)
        if p.scheme in ('https', 'http') and p.hostname and (keyword in title):
            items.append({'title': title, 'url': url})
    if not items and (not keyword):
        raise ValueError('未识别调查数据库导航')
    return {'source_url': BASE, 'items': items, 'note': '仅高校/研究机构公开数据库导航，目标站的可用性与权限须自行核对；不访问目标站。'}
