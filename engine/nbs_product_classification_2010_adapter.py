"""国家统计局 2010 年统计用产品分类目录的逐层浏览。"""
import release_runtime
import re
from urllib.parse import urljoin, urlsplit
import requests
from bs4 import BeautifulSoup
ROOT = 'https://www.stats.gov.cn/sj/tjbz/tjypflml/2010/'

def browse(url=ROOT + 'index.html', keyword=''):
    if not isinstance(url, str) or not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('输入无效')
    p = urlsplit(url)
    if p.scheme != 'https' or p.hostname != 'www.stats.gov.cn' or (not p.path.startswith('/sj/tjbz/tjypflml/2010/')) or ('..' in p.path.split('/')) or p.query or p.fragment or (not re.fullmatch('(?:[0-9]{2}/)*(?:index|[0-9]{2,10})\\.html', p.path.removeprefix('/sj/tjbz/tjypflml/2010/'))):
        raise ValueError('只接受 2010 年官方分类目录页面')
    r = requests.get(url, timeout=25, allow_redirects=False)
    r.raise_for_status()
    if r.is_redirect or len(r.content) > 5000000:
        raise ValueError('响应跳转或过大')
    r.encoding = 'gbk'
    s = BeautifulSoup(r.text, 'html.parser')
    items = []
    if p.path.endswith('/index.html'):
        for a in s.select('a[href]'):
            m = re.fullmatch('(\\d{2})-(.+)', a.get_text(' ', strip=True))
            if m and keyword in m.group(0):
                items.append({'code': m.group(1), 'name': m.group(2), 'url': urljoin(url, a['href'])})
    else:
        t = None
        for candidate in s.find_all('table'):
            rows = candidate.find_all('tr', recursive=False)
            if rows:
                cells = rows[0].find_all(['td', 'th'], recursive=False)
                if len(cells) >= 2 and cells[0].get_text(strip=True) == '代码' and (cells[1].get_text(strip=True) == '产品名称'):
                    t = candidate
                    break
        if not t:
            raise ValueError('未识别分类表')
        for row in t.find_all('tr', recursive=False)[1:]:
            cells = row.find_all(['td', 'th'], recursive=False)
            if len(cells) < 2:
                continue
            code = cells[0].get_text(' ', strip=True)
            name = cells[1].get_text(' ', strip=True)
            if not re.fullmatch('\\d{2,10}', code) or keyword not in code + name:
                continue
            a = cells[0].find('a', href=True) or cells[1].find('a', href=True)
            item = {'code': code, 'name': name, 'description': cells[2].get_text(' ', strip=True) if len(cells) > 2 else None, 'url': urljoin(url, a['href']) if a else None}
            items.append(item)
    return {'source': '国家统计局 2010 年统计用产品分类目录', 'source_url': url, 'keyword': keyword, 'items': items, 'note': '仅筛当前层级，返回分类而非统计观测值；这是历史版本，是否适用于当前业务应另查最新标准。'}
