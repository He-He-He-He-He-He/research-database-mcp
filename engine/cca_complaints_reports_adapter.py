"""Search selected public republications of China Consumers Association reports."""
import release_runtime
import requests
from bs4 import BeautifulSoup
SOURCES = {2022: {'url': 'https://amr.hunan.gov.cn/amr/ztx/qxcpzh/aqbz/202303/t20230314_29273535.html', 'publisher': '湖南省市场监督管理局', 'origin': '中国消费者协会', 'coverage': '年度分析全文转载（图表为图片时不搜索图中文字）', 'selector': 'div.text'}, 2023: {'url': 'https://cca.org.cn/single/11186/48152.html', 'publisher': '中国消费者协会', 'origin': '中国消费者协会', 'coverage': '年度分析原文（图表为图片时不搜索图中文字）', 'selector': '#content'}, 2024: {'url': 'https://finance.cnr.cn/zmn/tszn/20250207/t20250207_527064206.shtml', 'publisher': '央广网', 'origin': '中国消费者协会', 'coverage': '年度分析全文转载（图表为图片时不搜索图中文字）', 'selector': 'div.article-content'}, 2025: {'url': 'https://cca.org.cn/single/11186/62925.html', 'publisher': '中国消费者协会', 'origin': '中国消费者协会', 'coverage': '年度分析原文（图表为图片时不搜索图中文字）', 'selector': '#content'}}

def catalog():
    return [{'year': y, **v} for y, v in sorted(SOURCES.items())]

def search(year, keyword='', limit=20):
    if any((isinstance(v, bool) or not (isinstance(v, int) or (isinstance(v, str) and v.isascii() and v.isdigit())) for v in (year, limit))):
        raise ValueError('年份和 limit 须为整数')
    if not isinstance(keyword, str):
        raise ValueError('关键词须为字符串')
    year = int(year)
    if year not in SOURCES:
        raise ValueError('目前仅收录 2022–2025 年，未收录不代表原报告不存在')
    if not 1 <= int(limit) <= 200:
        raise ValueError('limit 必须在 1 到 200 之间')
    source = SOURCES[year]
    r = requests.get(source['url'], timeout=25)
    r.raise_for_status()
    r.encoding = r.apparent_encoding
    soup = BeautifulSoup(r.text, 'html.parser')
    body = soup.select_one(source['selector'])
    if body is None:
        raise RuntimeError('未找到正文，页面可能改版或不可用')
    paragraphs = []
    for p in body.find_all('p'):
        if p.find('p'):
            continue
        t = ' '.join(p.get_text('', strip=True).split())
        if t and (not keyword or keyword in t):
            paragraphs.append(t)
    return {'year': year, 'source': dict(source), 'keyword': keyword, 'matches': len(paragraphs), 'paragraphs': paragraphs[:int(limit)], 'scope': '全国消协组织受理投诉，不等同全国12315或所有消费纠纷。'}
