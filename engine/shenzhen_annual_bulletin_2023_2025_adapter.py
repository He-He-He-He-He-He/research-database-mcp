"""Shenzhen annual socio-economic bulletins, 2023–2025."""
import release_runtime
import subprocess
from urllib.parse import urljoin
from bs4 import BeautifulSoup
URLS = {2023: 'https://tjj.sz.gov.cn/gkmlpt/content/11/11264/post_11264245.html', 2024: 'https://tjj.sz.gov.cn/gkmlpt/content/12/12190/post_12190509.html', 2025: 'https://tjj.sz.gov.cn/zwgk/zfxxgkml/tjsj/tjgb/content/post_12803919.html'}

def bulletin(year, keyword=''):
    if year not in URLS:
        raise ValueError('available years: 2023, 2024, 2025')
    if not isinstance(keyword, str):
        raise ValueError('keyword must be a string')
    url = URLS[year]
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--max-time', '35', url], capture_output=True, timeout=40)
    if p.returncode:
        raise RuntimeError('official source failed: curl status ' + str(p.returncode))
    s = BeautifulSoup(p.stdout, 'html.parser')
    body = s.select_one('.TRS_Editor') or s.select_one('.article-content')
    if not body:
        raise ValueError('article body missing')
    paragraphs = [p.get_text('', strip=True) for p in body.find_all('p') if p.get_text('', strip=True) and keyword in p.get_text('', strip=True)]
    images = [urljoin(url, i['src']) for i in body.find_all('img', src=True)]
    if not paragraphs and (not keyword):
        raise ValueError('article text missing')
    return {'year': year, 'source': '深圳市统计局', 'source_url': url, 'paragraphs': paragraphs, 'image_urls': images}
