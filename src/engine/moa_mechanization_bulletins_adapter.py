"""National agricultural mechanization bulletins, official MOA pages."""
import release_runtime
import requests
from bs4 import BeautifulSoup
SOURCES = {2022: 'https://njhs.moa.gov.cn/nyjxhqk/202406/t20240618_6457395.htm', 2023: 'https://njhs.moa.gov.cn/nyjxhqk/202511/t20251120_6479054.htm', 2024: 'https://njhs.moa.gov.cn/nyjxhqk/202511/t20251120_6479055.htm'}

def catalog():
    return [{'year': y, 'url': url, 'publisher': '农业农村部农业机械化管理司'} for y, url in sorted(SOURCES.items())]

def read(year, keyword='', limit=30):
    year = int(year)
    if year not in SOURCES:
        raise ValueError('年份未收录，不表示公报不存在')
    if not 1 <= int(limit) <= 200:
        raise ValueError('limit 必须在 1 至 200 之间')
    r = requests.get(SOURCES[year], timeout=25)
    r.raise_for_status()
    r.encoding = r.apparent_encoding
    body = BeautifulSoup(r.text, 'html.parser').select_one('.TRS_Editor')
    if body is None:
        raise RuntimeError('未找到正文')
    paragraphs = []
    for p in body.find_all('p'):
        if p.find_parent('table') or p.find('p'):
            continue
        text = p.get_text('', strip=True)
        if text and keyword in text:
            paragraphs.append(text)
    tables = []
    for t in body.find_all('table'):
        rows = []
        for tr in t.find_all('tr'):
            cells = tr.find_all(['th', 'td'], recursive=False)
            if cells:
                rows.append([c.get_text('', strip=True) for c in cells])
        if rows:
            tables.append(rows)
    return {'year': year, 'url': SOURCES[year], 'publisher': '农业农村部农业机械化管理司', 'keyword': keyword, 'matches': len(paragraphs), 'paragraphs': paragraphs[:int(limit)], 'tables': tables, 'note': '表格返回原始行列，不处理合并单元格；指标定义与跨年口径请查原文。'}
