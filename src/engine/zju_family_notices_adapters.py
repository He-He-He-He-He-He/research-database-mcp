"""浙大中国家庭大数据库公开通知列表及正文；不申请或访问调查微观数据。"""
import release_runtime
import re
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
BASE = 'https://ssec.zju.edu.cn/zgjtdsjk/list.htm'
PATH = re.compile('/\\d{4}/\\d{4}/c86173a\\d+/page\\.htm')

def _get(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'ssec.zju.edu.cn' or p.query or p.fragment or (not (p.path == '/zgjtdsjk/list.htm' or PATH.fullmatch(p.path))):
        raise ValueError('仅支持浙大家庭数据库通知栏目')
    r = requests.get(url, timeout=20, allow_redirects=False)
    if r.status_code != 200:
        raise RuntimeError('上游 HTTP ' + str(r.status_code))
    r.encoding = 'utf-8'
    return BeautifulSoup(r.text, 'html.parser')

def zju_family_notices(keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('关键词不超过100字')
    s = _get(BASE)
    items = []
    recognized = False
    for a in s.select('a.box[href]'):
        href = urljoin(BASE, a['href'])
        p = urlparse(href)
        h = a.select_one('h4.title')
        if p.hostname != 'ssec.zju.edu.cn' or not PATH.fullmatch(p.path) or (not h):
            continue
        title = h.get_text(' ', strip=True)
        if not title:
            continue
        recognized = True
        if keyword not in title:
            continue
        year = a.select_one('.year')
        day = a.select_one('.concrete')
        items.append({'title': title, 'url': href, 'date': f'{year.get_text(strip=True)}-{day.get_text(strip=True)}' if year and day else None})
    if not recognized:
        raise ValueError('未识别通知列表，无法确认检索结果')
    return items

def zju_family_notice_detail(url):
    s = _get(url)
    body = s.select_one('.wp_articlecontent')
    if not body or not s.title:
        raise ValueError('未识别通知正文')
    text = body.get_text('\n', strip=True)
    if len(text) < 100:
        raise ValueError('通知正文过短')
    return {'url': url, 'title': s.title.get_text(strip=True), 'text': text, 'note': '公开历史通知；访问条件和流程可能变化，不代表获准使用微观数据。'}
