"""读取国家哲学社会科学文献中心资助期刊栏目当前页。"""
import release_runtime
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
URL = 'https://www.ncpssd.cn/journal/fund'

def ncpssd_funded_journals(keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('关键词须不超过100字')
    r = requests.get(URL, timeout=20, allow_redirects=False)
    r.raise_for_status()
    s = BeautifulSoup(r.text, 'html.parser')
    if not s.find(string=lambda x: x and '国家社科基金资助期刊' in x):
        raise ValueError('未识别资助期刊栏目')
    rows = []
    for li in s.select('li.imgone'):
        a = li.select_one('a.j-title[href]')
        if not a:
            continue
        url = urljoin(URL, a['href'])
        p = urlparse(url)
        if p.hostname != 'www.ncpssd.cn' or p.path != '/journal/secure/details':
            raise ValueError('期刊详情链接不属于指定栏目')
        title = a.get_text(' ', strip=True)
        fallback = li.select_one('.beiyong p:last-child')
        if title:
            rows.append({'title': title, 'identifier': li.get('data-val'), 'issue_label': fallback.get_text(' ', strip=True) if fallback else None, 'url': url})
    if not rows:
        raise ValueError('未识别期刊列表')
    q = keyword.strip().casefold()
    return {'source': '国家哲学社会科学文献中心国家社科基金资助期刊栏目', 'source_url': URL, 'keyword': keyword, 'items': [x for x in rows if q in x['title'].casefold()], 'note': '只读取栏目当前页标题并本地筛选，期次为页面显示值；非全量期刊、文章检索或全文权限。'}
