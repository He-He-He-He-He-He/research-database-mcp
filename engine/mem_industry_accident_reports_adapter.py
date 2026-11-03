"""MEM official 2024/2025 industry accident analysis articles."""
import release_runtime
import requests
from bs4 import BeautifulSoup
BASE = 'https://www.mem.gov.cn/xw/yjglbgzdt/'
SOURCES = {2024: {'冶金': '202505/t20250507_531444.shtml'}, 2025: {'建材': '202604/t20260407_599406.shtml', '机械': '202604/t20260407_599408.shtml'}}

def catalogue():
    return [{'year': y, 'industry': name, 'url': BASE + path} for y, entries in SOURCES.items() for name, path in entries.items()]

def report(year, industry, keyword=''):
    if isinstance(year, bool) or year not in SOURCES or industry not in SOURCES[year]:
        raise ValueError('unsupported year or industry')
    url = BASE + SOURCES[year][industry]
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    body = s.select_one('.TRS_Editor')
    if body is None or not body.get_text(strip=True):
        raise ValueError('report body missing')
    all_text = [p.get_text(' ', strip=True) for p in body.select('p') if p.get_text(' ', strip=True)]
    if not all_text:
        raise ValueError('no paragraphs')
    return {'year': year, 'industry': industry, 'source_url': url, 'paragraphs': [p for p in all_text if keyword.casefold() in p.casefold()]}
