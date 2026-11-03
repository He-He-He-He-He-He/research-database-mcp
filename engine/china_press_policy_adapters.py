"""中国记者网政策法规目录及原文。"""
import release_runtime
import re
from urllib.parse import urljoin, urlsplit
from nppa_statistics_adapters import fetch
from nppa_regulations_adapters import _Body
from szse_chinext_adapters import _Links
BASE = 'https://press.nppa.gov.cn/zcfg/'

def china_press_policy_list(page=1, keyword=''):
    if isinstance(page, bool) or not (isinstance(page, int) or (isinstance(page, str) and page.isascii() and page.isdigit())):
        raise ValueError('页码须为整数')
    page = int(page)
    if not 1 <= page <= 100:
        raise ValueError('页码须为 1—100')
    if not isinstance(keyword, str):
        raise ValueError('关键词须为字符串')
    url = BASE + ('index.html' if page == 1 else f'index_{page - 1}.html')
    parser = _Links()
    parser.feed(fetch(url).decode('utf-8'))
    rows = []
    for href, title in parser.links:
        link = urljoin(url, href)
        if re.fullmatch(re.escape(BASE) + '\\d{6}/t\\d{8}_\\d+\\.html', link):
            rows.append({'title': ' '.join(title.split()), 'url': link})
    if not rows:
        raise ValueError('未识别目录，可能超出页数或网站改版')
    return {'page': page, 'source_url': url, 'items': [r for r in rows if keyword.casefold() in r['title'].casefold()], 'scope': '只筛选当前页标题；历史发布文本的效力及修订须另行核查。'}

def china_press_policy_detail(url):
    if not re.fullmatch(re.escape(BASE) + '\\d{6}/t\\d{8}_\\d+\\.html', url):
        raise ValueError('仅允许中国记者网政策法规栏目文章')
    raw = fetch(url).decode('utf-8')
    parser = _Body('trs_editor_view')
    parser.feed(raw)
    text = '\n'.join((line.strip() for line in ''.join(parser.text).splitlines() if line.strip()))
    if not parser.found or len(text) < 100:
        raise ValueError('未识别正文')
    links = _Links()
    links.feed(raw)
    attachments = []
    for href, _ in links.links:
        link = urljoin(url, href)
        p = urlsplit(link)
        if p.scheme == 'https' and p.hostname == 'press.nppa.gov.cn' and p.path.lower().endswith(('.pdf', '.doc', '.docx', '.xls', '.xlsx')) and (link not in attachments):
            attachments.append(link)
    return {'source_url': url, 'text': text, 'attachments': attachments, 'note': '政策转载页；发布、施行时间及后续效力须查原文与发布机关最新文件。'}
