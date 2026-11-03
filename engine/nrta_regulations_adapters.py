"""国家广播电视总局公开法规规章目录与正文。"""
import release_runtime
import html
import re
from urllib.parse import urljoin, urlsplit
from nrta_announcements_adapters import fetch, Body
CATEGORIES = {'rules': ('部门规章', 1588), 'normative': ('规范性文件', 2062), 'regulations': ('法规', 2060), 'state_council': ('国务院文件', 3745)}

def nrta_regulations_list(category='rules', keyword=''):
    if category not in CATEGORIES:
        raise ValueError('category 须为 rules、normative、regulations 或 state_council')
    name, col = CATEGORIES[category]
    url = f'https://www.nrta.gov.cn/col/col{col}/index.html'
    page = fetch(url)
    pattern = '<a\\s+href="(https://www\\.nrta\\.gov\\.cn/art/\\d{4}/\\d{1,2}/\\d{1,2}/art_' + str(col) + '_\\d+\\.html)"([^>]*)>(.*?)</a>'
    rows = []
    for link, attrs, content in re.findall(pattern, page, re.S):
        title_match = re.search('\\btitle="([^"]+)"', attrs)
        title = html.unescape(title_match.group(1) if title_match else re.sub('<[^>]+>', '', content)).strip()
        if keyword.casefold() in title.casefold() and (not any((x['url'] == link for x in rows))):
            rows.append({'title': title, 'url': link})
    if not rows and (not keyword):
        raise ValueError('未识别目录，网站可能改版')
    return {'category': name, 'source_url': url, 'items': rows, 'scope': '只读取栏目首页内嵌条目；部分标题截断，完整标题请查详情；不保证全量和效力状态。'}

def nrta_regulations_detail(url):
    p = urlsplit(url)
    cols = '|'.join((str(c) for _, c in CATEGORIES.values()))
    if p.scheme != 'https' or p.hostname != 'www.nrta.gov.cn' or p.query or p.fragment or (not re.fullmatch('/art/\\d{4}/\\d{1,2}/\\d{1,2}/art_(?:' + cols + ')_\\d+\\.html', p.path)):
        raise ValueError('仅允许四个栏目内的官网文章地址')
    parser = Body()
    parser.feed(fetch(url))
    text = '\n'.join((x.strip() for x in ''.join(parser.parts).splitlines() if x.strip()))
    if not parser.title or not text:
        raise ValueError('未识别原文正文')
    links = []
    for h in parser.links:
        link = urljoin(url, h)
        x = urlsplit(link)
        if x.scheme == 'https' and x.hostname == 'www.nrta.gov.cn' and x.path.lower().endswith(('.pdf', '.doc', '.docx', '.xls', '.xlsx')):
            links.append(link)
    return {'title': parser.title, 'source_url': url, 'text': text, 'attachments': links, 'note': '页面为发布原文，不自动判定效力、后续修订或附件内容。'}
