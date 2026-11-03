"""最高检四大检察工作白皮书跨年度目录与正文段落检索。"""
import release_runtime
import re
from urllib.parse import urljoin, urlsplit
import requests
from bs4 import BeautifulSoup
INDEX = 'https://www.spp.gov.cn/spp/bps/index.shtml'
CATS = ('刑事', '民事', '行政', '公益诉讼')

def _get(url):
    with requests.get(url, timeout=(10, 25), allow_redirects=False, stream=True) as r:
        r.raise_for_status()
        if r.is_redirect:
            raise ValueError('上游重定向')
        out = bytearray()
        for chunk in r.iter_content(65536):
            out.extend(chunk)
            if len(out) > 5000000:
                raise ValueError('文档超出大小上限')
        return bytes(out)

def catalog():
    soup = BeautifulSoup(_get(INDEX), 'html.parser')
    items = []
    for a in soup.select('a[href]'):
        title = (a.get('title') or a.get_text(' ', strip=True)).strip()
        m = re.fullmatch('(刑事|民事|行政|公益诉讼)检察工作白皮书[（(](20\\d{2})[）)]', title)
        u = urljoin(INDEX, a['href'])
        p = urlsplit(u)
        if m and p.scheme == 'https' and (p.hostname == 'www.spp.gov.cn') and re.fullmatch('/xwfbh/wsfbh/\\d{6}/t\\d{8}_\\d+\\.shtml', p.path):
            items.append({'year': int(m[2]), 'category': m[1], 'title': title, 'url': u})
    if not items:
        raise ValueError('未识别白皮书目录')
    return {'source': '最高人民检察院四大检察工作白皮书', 'source_url': INDEX, 'items': items, 'note': '仅目录中刑事、民事、行政、公益诉讼四类，非全部检察统计；年度口径以原文为准。'}

def search(year, category, keyword='', limit=30):
    if isinstance(year, bool) or not isinstance(year, int):
        raise ValueError('year 必须是整数')
    if category not in CATS:
        raise ValueError('category 为 刑事、民事、行政或公益诉讼')
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('keyword 最多 100 字')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 200):
        raise ValueError('limit 须为 1–200')
    item = next((i for i in catalog()['items'] if i['year'] == year and i['category'] == category), None)
    if not item:
        raise ValueError('该年度类别未在目录中')
    s = BeautifulSoup(_get(item['url']), 'html.parser')
    body = s.select_one('#fontzoom')
    if not body:
        raise ValueError('正文结构改变')
    paras = [re.sub('\\s+', ' ', p.get_text('', strip=True)).strip() for p in body.select('p')]
    paras = [p for p in paras if p]
    if len(paras) < 5:
        raise ValueError('未识别有效正文')
    hits = [{'paragraph': i + 1, 'text': p} for i, p in enumerate(paras) if keyword in p]
    return {'source': '最高人民检察院四大检察工作白皮书', **item, 'keyword': keyword, 'total_paragraphs': len(paras), 'matched_paragraphs': len(hits), 'hits': hits[:limit], 'note': '按正文段落匹配，不自动计算或合并数值；案件、人数、案次与受理和办结等指标不同，应核对原文指标定义、年期及脚注。'}
