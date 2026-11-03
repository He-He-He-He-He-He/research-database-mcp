"""文化和旅游部市场管理公开信息目录与正文。"""
import release_runtime
import re
from urllib.parse import urljoin, urlsplit
from mct_statistics_adapters import fetch, Body
from szse_chinext_adapters import _Links
BASE = 'https://zwgk.mct.gov.cn'
INDEX = BASE + '/zfxxgkml/447/496/'

def mct_market_management_list(page=1, keyword=''):
    page = int(page)
    if not 1 <= page <= 100:
        raise ValueError('页码须为 1—100')
    url = INDEX + ('index_3081.html' if page == 1 else f'index_3081_{page - 1}.html')
    parser = _Links()
    parser.feed(fetch(url))
    rows = []
    for href, title in parser.links:
        link = urljoin(url, href)
        p = urlsplit(link)
        if p.scheme == 'https' and p.hostname == 'zwgk.mct.gov.cn' and re.fullmatch('/zfxxgkml/scgl/\\d{6}/t\\d{8}_\\d+\\.html', p.path):
            rows.append({'title': ' '.join(title.split()), 'url': link})
    if not rows:
        raise ValueError('未识别目录，可能超出页数或网站改版')
    return {'page': page, 'source_url': url, 'items': [r for r in rows if keyword.casefold() in r['title'].casefold()], 'scope': '关键词只筛选本页标题；栏目混有通知、公告、公示和政策解读。'}

def mct_market_management_detail(url):
    p = urlsplit(url)
    if p.scheme != 'https' or p.hostname != 'zwgk.mct.gov.cn' or p.query or p.fragment or (not re.fullmatch('/zfxxgkml/scgl/\\d{6}/t\\d{8}_\\d+\\.html', p.path)):
        raise ValueError('仅允许市场管理栏目文章')
    raw = fetch(url)
    parser = Body()
    parser.feed(raw)
    text = '\n'.join((line.strip() for line in ''.join(parser.parts).splitlines() if line.strip()))
    if len(text) < 100:
        raise ValueError('未识别正文')
    links = _Links()
    links.feed(raw)
    attachments = []
    for href, _ in links.links:
        link = urljoin(url, href)
        x = urlsplit(link)
        if x.scheme == 'https' and x.hostname == 'zwgk.mct.gov.cn' and x.path.lower().endswith(('.pdf', '.doc', '.docx', '.xls', '.xlsx')) and (link not in attachments):
            attachments.append(link)
    images = [urljoin(url, s) for s in parser.images if urlsplit(urljoin(url, s)).hostname == 'zwgk.mct.gov.cn']
    return {'source_url': url, 'published': parser.published, 'text': text, 'attachments': attachments, 'images': images, 'note': '原文可能为历史或征求意见内容；效力、适用时点、附件与图片须核对原文。'}
