"""Two publicly reprinted SAMR national special equipment safety reports."""
import release_runtime
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
SOURCES = {2024: {'url': 'https://www.yncj.gov.cn/cjxzfxxgk/aqsj1525/20250620/1608266.html', 'selector': '.zt_xilan_07', 'host': '澄江市人民政府', 'official_url': 'https://www.samr.gov.cn/tzsbj/qktb/tb/art/2025/art_1b31b22095744942af16cf24cec957ac.html'}, 2025: {'url': 'https://sdtj.sdic.com.cn/sdtjn/xxzx/hydc/webinfo/2026/05/1776119448419928.htm', 'selector': '#BodyLabel', 'host': '国投检测股份有限公司', 'official_url': 'https://www.samr.gov.cn/tzsbj/qktb/tb/art/2026/art_2097ad373c6543218a2d3fc110d84caa.html'}}

def catalogue():
    return [{'year': y, **{k: v for k, v in item.items() if k != 'selector'}} for y, item in SOURCES.items()]

def report(year, keyword=''):
    if isinstance(year, bool) or year not in SOURCES:
        raise ValueError('available years: 2024, 2025')
    source = SOURCES[year]
    r = requests.get(source['url'], timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.content, 'html.parser')
    body = soup.select_one(source['selector'])
    if body is None or '特种设备' not in body.get_text():
        raise ValueError('report body missing')
    paragraphs = [p.get_text(' ', strip=True) for p in body.select('p') if p.get_text(' ', strip=True) and keyword.casefold() in p.get_text(' ', strip=True).casefold()]
    images = [urljoin(source['url'], x['src']) for x in body.select('img[src]')]
    return {'year': year, 'source_url': source['url'], 'reprint_host': source['host'], 'official_url': source['official_url'], 'paragraphs': paragraphs, 'image_urls': images}
