"""人大复印报刊资料校园 IP 的单篇题录、摘要和来源字段。"""
import release_runtime
import re
import xml.etree.ElementTree as ET
import requests
from bs4 import BeautifulSoup
from rdfybk_institution_catalog_adapter import BASE

def _record(content):
    try:
        root = ET.fromstring(content)
    except ET.ParseError:
        raise RuntimeError('站方详情 XML 异常') from None
    records = root.findall('R1')
    if len(records) != 1:
        raise RuntimeError('站方详情记录数量异常')
    row = {}
    for node in records[0]:
        if node.tag in row:
            raise RuntimeError('站方详情字段重复')
        row[node.tag] = ''.join(node.itertext()).strip() or None
    return row

def detail(article_id, expected_title):
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
        base = _record(r.content)
        if base.get('til') != expected_title.strip():
            raise RuntimeError('站方返回的文章标题与请求不匹配')
        r = s.get(BASE + 'Qw/GetSrcPdc/' + article_id, timeout=20)
        r.raise_for_status()
        periodical = _record(r.content)
    return {'source': '人大复印报刊资料', 'institution': '浙江大学', 'requested_id': article_id, 'title': base['til'], 'base_fields': base, 'journal_fields': periodical, 'note': '原站未在详情响应回显文章 ID，已核对标题；原始字段和空值按站方返回保留。摘要和期刊信息不等于全文或逐篇授权，转载关系需核对。'}
