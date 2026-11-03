"""Selected national food inspection reports reproduced by China Food Safety News."""
import release_runtime
import requests
from bs4 import BeautifulSoup
SOURCES = {2022: ('https://www.cfsn.cn/news/detail/22/213454.html', '报道，非原通告完整附件'), 2023: ('https://www.cfsn.cn/news/detail/29/244698.html', '市场监管总局通告转载，未包含原附件表'), 2024: ('https://www.cfsn.cn/news/detail/22/305542.html', '市场监管总局情况通报转载'), 2025: ('https://www.cfsn.cn/news/detail/29/343441.html', '市场监管总局情况通报转载')}

def catalog():
    return [{'year': y, 'url': u, 'coverage': c, 'publisher': '中国食品安全网', 'original_author': '国家市场监督管理总局'} for y, (u, c) in sorted(SOURCES.items())]

def search(year, keyword='', limit=20):
    year = int(year)
    if year not in SOURCES:
        raise ValueError('未收录该年份，不代表没有报告')
    if not 1 <= int(limit) <= 200:
        raise ValueError('limit 应在 1 至 200 之间')
    url, coverage = SOURCES[year]
    r = requests.get(url, timeout=25)
    r.raise_for_status()
    r.encoding = r.apparent_encoding
    body = BeautifulSoup(r.text, 'html.parser').select_one('.newShow .content')
    if body is None:
        raise RuntimeError('来源页面正文缺失或已改版')
    paragraphs = [p.get_text('', strip=True) for p in body.find_all('p') if not p.find('p') and p.get_text('', strip=True) and (keyword in p.get_text('', strip=True))]
    return {'year': year, 'url': url, 'coverage': coverage, 'publisher': '中国食品安全网', 'original_author': '国家市场监督管理总局', 'keyword': keyword, 'matches': len(paragraphs), 'paragraphs': paragraphs[:int(limit)], 'note': '问题导向监督抽检，不合格率不代表市场全部食品的不合格率。'}
