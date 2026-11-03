"""NNSA-hosted Chinese nuclear energy association operating reports."""
import release_runtime
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
URLS = {2021: 'https://nnsa.mee.gov.cn/ywdt/hyzx/202303/t20230320_1020233.html', 2024: 'https://nnsa.mee.gov.cn/ywdt/hyzx/202502/t20250206_1101794.html', 2025: 'https://nnsa.mee.gov.cn/ywdt/hyzx/202602/t20260206_1143783.html'}

def catalogue():
    return [{'year': y, 'url': u} for y, u in URLS.items()]

def report(year, keyword=''):
    if isinstance(year, bool) or year not in URLS:
        raise ValueError('available years: 2021, 2024, 2025')
    url = URLS[year]
    r = requests.get(url, timeout=30, headers={'User-Agent': 'ResearchDatabaseToolkit/1.0'})
    r.raise_for_status()
    soup = BeautifulSoup(r.content, 'html.parser')
    body = soup.select_one('.TRS_Editor')
    if body is None:
        raise ValueError('report body not found')
    paragraphs = []
    for node in body.find_all(['p', 'div'], recursive=False):
        text = node.get_text(' ', strip=True)
        if text and keyword.casefold() in text.casefold():
            paragraphs.append(text)
    if not body.get_text(strip=True):
        raise ValueError('report body empty')
    images = [urljoin(url, img['src']) for img in body.select('img[src]')]
    return {'year': year, 'source_url': url, 'publisher': '国家核安全局网站', 'origin': '中国核能行业协会', 'paragraphs': paragraphs, 'image_urls': images}
