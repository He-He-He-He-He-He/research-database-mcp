"""人大复印报刊资料单篇文章站方参考文献列表。"""
import release_runtime
import re
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from rdfybk_institution_catalog_adapter import BASE
from rdfybk_institution_detail_adapter import _record

def references(article_id, expected_title):
    if isinstance(article_id, bool) or not str(article_id).isdigit() or (not 1 <= int(article_id) <= 999999999999):
        raise ValueError('文章编号须为正整数')
    if not isinstance(expected_title, str) or not expected_title.strip() or len(expected_title) > 300:
        raise ValueError('须提供完整文章标题')
    article_id = str(article_id)
    with requests.Session() as s:
        r = s.get(BASE, timeout=20)
        r.raise_for_status()
        if not re.search('浙江大学\\s+退出', BeautifulSoup(r.content, 'html.parser').get_text(' ', strip=True)):
            raise RuntimeError('未确认浙江大学机构会话')
        r = s.get(BASE + 'Qw/GetBaseArt', params={'id': article_id, 'kw': ''}, timeout=20)
        r.raise_for_status()
        meta = _record(r.content)
        if meta.get('til') != expected_title.strip():
            raise RuntimeError('文章标题与请求不匹配')
        r = s.get(BASE + 'Qw/GetReferenceList/' + article_id, params={'kw': ''}, timeout=20)
        r.raise_for_status()
    try:
        root = ET.fromstring(r.content)
    except ET.ParseError:
        raise RuntimeError('参考文献响应 XML 异常') from None
    if root.tag != 'D':
        raise RuntimeError('参考文献响应结构异常')
    rows = []
    for row in root.findall('R1'):
        cite = row.find('ck')
        cid = row.find('cid')
        if cite is None:
            raise RuntimeError('参考文献字段缺失')
        rows.append({'reference_id': ''.join(cid.itertext()).strip() if cid is not None else None, 'text_raw': ''.join(cite.itertext()).strip()})
    return {'source': '人大复印报刊资料', 'institution': '浙江大学', 'requested_id': article_id, 'title': meta['til'], 'references': rows, 'note': '站方返回的参考文献原始条目；空列表仅表示该接口未返回条目，不能断言原文没有参考文献。响应未回显文章编号，已核对标题；文献信息须回查原始出处。'}
