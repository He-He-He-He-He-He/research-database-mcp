"""中国信息安全测评中心政策法规公开目录。"""
import release_runtime
import re
from urllib.parse import urljoin, urlsplit
from nppa_statistics_adapters import fetch
from nppa_regulations_adapters import _Body
from szse_chinext_adapters import _Links
ROOT = 'https://www.itsec.gov.cn/fgbz/'
CATEGORIES = {'law': 'gjbz', 'administrative': 'xgfg', 'ministerial': 'gjibz', 'policy': 'pgyj'}

def itsec_network_policy_list(category='ministerial', page=1, keyword=''):
    page = int(page)
    if category not in CATEGORIES or not 1 <= page <= 100:
        raise ValueError('分类或页码无效')
    base = ROOT + CATEGORIES[category] + '/'
    url = base if page == 1 else urljoin(base, f'index_{page - 1}.html')
    parser = _Links()
    parser.feed(fetch(url).decode('utf-8'))
    rows = []
    for href, title in parser.links:
        link = urljoin(url, href)
        if re.fullmatch(re.escape(base) + '\\d{6}/t\\d{8}_\\d+\\.html', link):
            rows.append({'title': ' '.join(title.split()), 'url': link})
    if not rows:
        raise ValueError('未识别目录，可能超出页数或网站改版')
    return {'category': category, 'page': page, 'source_url': url, 'items': [x for x in rows if keyword.casefold() in x['title'].casefold()], 'scope': '只筛选当前页标题，转载文本的现行效力和后续修订须另行核查。'}

def itsec_network_policy_detail(url):
    if not re.fullmatch(re.escape(ROOT) + '(?:gjbz|xgfg|gjibz|pgyj)/\\d{6}/t\\d{8}_\\d+\\.html', url):
        raise ValueError('仅允许以上栏目内文章')
    raw = fetch(url).decode('utf-8')
    parser = _Body('content2')
    parser.feed(raw)
    text = '\n'.join((s.strip() for s in ''.join(parser.text).splitlines() if s.strip()))
    if not parser.found or len(text) < 100:
        raise ValueError('未识别正文')
    links = _Links()
    links.feed(raw)
    attachments = []
    for href, _ in links.links:
        link = urljoin(url, href)
        p = urlsplit(link)
        if p.scheme == 'https' and p.hostname == 'www.itsec.gov.cn' and p.path.lower().endswith(('.pdf', '.doc', '.docx', '.xls', '.xlsx')) and (link not in attachments):
            attachments.append(link)
    return {'source_url': url, 'text': text, 'attachments': attachments, 'note': '转载页面；具体颁布机关、施行日期和后续修订以权威原文为准。'}
