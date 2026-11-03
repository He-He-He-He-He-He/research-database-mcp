"""文化和旅游部规范性文件分页目录及正文。"""
import release_runtime
import re
import subprocess
from urllib.parse import urljoin, urlsplit
from szse_chinext_adapters import _Links
from nppa_regulations_adapters import _Body
BASE = 'https://zwgk.mct.gov.cn/zfxxgkml/zcfg/gfxwj/'

def _get(url):
    p = urlsplit(url)
    if p.scheme != 'https' or p.hostname != 'zwgk.mct.gov.cn' or (not p.path.startswith('/zfxxgkml/zcfg/gfxwj/')) or p.query or p.fragment:
        raise ValueError('仅允许文化和旅游部规范性文件栏目')
    return release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '20', url], check=True, capture_output=True).stdout.decode('utf-8')

def mct_normative_documents_list(page=1, keyword=''):
    page = int(page)
    if not 1 <= page <= 100:
        raise ValueError('页码须为 1—100')
    url = BASE if page == 1 else urljoin(BASE, f'index_{page - 1}.html')
    parser = _Links()
    parser.feed(_get(url))
    all_items = []
    for href, title in parser.links:
        link = urljoin(BASE, href)
        if re.fullmatch(re.escape(BASE) + '\\d{6}/t\\d{8}_\\d+\\.html', link):
            all_items.append({'title': ' '.join(title.split()), 'url': link})
    if not all_items:
        raise ValueError('未识别目录，可能超出页数或网站改版')
    return {'page': page, 'source_url': url, 'items': [x for x in all_items if keyword.casefold() in x['title'].casefold()], 'scope': '只筛选指定页标题，现行效力及后续变化请核查原文与最新清理公告。'}

def mct_normative_documents_detail(url):
    if not re.fullmatch(re.escape(BASE) + '\\d{6}/t\\d{8}_\\d+\\.html', url):
        raise ValueError('仅允许本栏目文章链接')
    raw = _get(url)
    parser = _Body('gsj_htmlcon_bot')
    parser.feed(raw)
    text = '\n'.join((line.strip() for line in ''.join(parser.text).splitlines() if line.strip()))
    if not parser.found or len(text) < 100:
        raise ValueError('未识别正文')
    links = _Links()
    links.feed(raw)
    attachments = []
    for href, _ in links.links:
        u = urljoin(url, href)
        p = urlsplit(u)
        if p.scheme == 'https' and p.hostname == 'zwgk.mct.gov.cn' and p.path.lower().endswith(('.pdf', '.doc', '.docx', '.xls', '.xlsx')) and (u not in attachments):
            attachments.append(u)
    return {'source_url': url, 'text': text, 'attachments': attachments, 'note': '仅返回正文和附件链接；政策的施行、修改和废止须查原文及后续公告。'}
