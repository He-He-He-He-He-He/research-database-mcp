"""人大复印报刊资料校园会话单篇文章的原站分页文字。"""
import release_runtime
import re
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from rdfybk_institution_catalog_adapter import BASE
from rdfybk_institution_detail_adapter import _record

def content(article_id, expected_title, page=1):
    if isinstance(article_id, bool) or not str(article_id).isdigit() or (not 1 <= int(article_id) <= 999999999999):
        raise ValueError('文章编号须为正整数')
    if not isinstance(expected_title, str) or not expected_title.strip() or len(expected_title) > 300:
        raise ValueError('须提供完整文章标题')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 1000):
        raise ValueError('页码须为 1–1000')
    article_id = str(article_id)
    with requests.Session() as s:
        r = s.get(BASE, timeout=20)
        r.raise_for_status()
        if not re.search('浙江大学\\s+退出', BeautifulSoup(r.content, 'html.parser').get_text(' ', strip=True)):
            raise RuntimeError('未确认浙江大学机构会话')
        r = s.get(BASE + 'Qw/GetBaseArt', params={'id': article_id, 'kw': ''}, timeout=20)
        r.raise_for_status()
        metadata = _record(r.content)
        if metadata.get('til') != expected_title.strip():
            raise RuntimeError('文章标题与请求不匹配')
        r = s.get(BASE + 'Qw/GetTextArt', params={'id': article_id, 'pn': str(page), 'ps': '2', 'kw': '', 'openall': '0'}, timeout=20)
        r.raise_for_status()
    try:
        root = ET.fromstring(r.content)
    except ET.ParseError:
        raise RuntimeError('正文响应 XML 异常') from None
    blocks = root.findall('R1')
    cnt = root.findall('R2/RC')
    if len(cnt) != 1 or not (cnt[0].text or '').isdigit() or len(blocks) > 2:
        raise RuntimeError('正文分页响应异常')
    total = int(cnt[0].text)
    text = []
    for row in blocks:
        node = row.find('ctt')
        if node is None:
            raise RuntimeError('正文段落缺失')
        text.append(''.join(node.itertext()))
    if not text and total > 0 and ((page - 1) * 2 < total):
        raise RuntimeError('站方未返回预期正文段落')
    return {'source': '人大复印报刊资料', 'institution': '浙江大学', 'requested_id': article_id, 'title': metadata['til'], 'page': page, 'segment_count_total': total, 'segments': text, 'note': '站方阅读器每页两段，计数为站方段落数而非印刷页数；原样保留段落中可能出现的 HTML。详情与正文响应均未回显 ID，已核对完整标题；实际逐篇访问以当前会话为准。'}
