"""Official annual lawyer and grassroots legal services statistical analyses."""
import release_runtime
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
BASE = 'https://www.moj.gov.cn/pub/sfbgw/zwxxgk/fdzdgknr/fdzdgknrtjxx/'
PATHS = {2019: '202006/t20200622_350049.html', 2020: '202106/t20210611_427394.html', 2021: '202208/t20220815_461680.html', 2022: '202306/t20230614_480740.html'}

def report(year, keyword=''):
    if year not in PATHS:
        raise ValueError('available years: 2019, 2020, 2021, 2022')
    if not isinstance(keyword, str):
        raise ValueError('keyword must be a string')
    url = BASE + PATHS[year]
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')
    body = soup.select_one('.TRS_Editor') or soup.select_one('.lCont')
    if body is None:
        raise ValueError('article body missing')
    blocks = []
    for p in body.find_all('p'):
        text = p.get_text('', strip=True)
        if text and keyword.casefold() in text.casefold():
            blocks.append(text)
    images = [urljoin(url, img['src']) for img in body.find_all('img', src=True)]
    if not blocks and (not keyword):
        raise ValueError('article text missing')
    return {'year': year, 'source': '中华人民共和国司法部', 'source_url': url, 'paragraphs': blocks, 'images': images}
