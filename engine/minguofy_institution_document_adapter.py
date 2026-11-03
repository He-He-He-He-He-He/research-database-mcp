"""书同文民国风云搜索结果的站方正常详情，保持段落次序。"""
import release_runtime
import re, requests, xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
BASE = 'https://gujiku.unihan.com.cn/'

def document(keyword, offset, expected_title):
    if not isinstance(keyword, str) or not 1 <= len(keyword.strip()) <= 100 or any((ord(c) < 32 or c == '+' for c in keyword)):
        raise ValueError('关键词须为1–100字单行文本且不含加号')
    if type(offset) is not int or not 0 <= offset <= 100000:
        raise ValueError('offset 无效')
    if not isinstance(expected_title, str) or not 1 <= len(expected_title.strip()) <= 300 or any((ord(c) < 32 for c in expected_title)):
        raise ValueError('须提供结果中的完整标题')
    q = keyword.strip()
    title = expected_title.strip()
    try:
        with requests.Session() as s:
            r = s.get(BASE + 'Products/Search/QSL', timeout=20)
            r.raise_for_status()
            if not re.search('\\bzjdx\\b', BeautifulSoup(r.content, 'html.parser').get_text(' ', strip=True), re.I):
                raise RuntimeError('未确认书同文学校账户标记')
            r = s.get(BASE + 'minguofy/api/oldsearch/MinGuoSearchContent', params={'word': q, 'start': offset, 'count': 1}, timeout=20)
            r.raise_for_status()
            d = r.json()
            if not isinstance(d, dict) or d.get('searchStr') != q or d.get('start') != offset or (d.get('count') != 1) or (not isinstance(d.get('items'), list)) or (len(d['items']) != 1):
                raise RuntimeError('检索结果或起始位置未确认')
            x = d['items'][0]
            if not isinstance(x, dict) or not isinstance(x.get('title'), str) or BeautifulSoup(x['title'], 'html.parser').get_text('', strip=True) != title:
                raise RuntimeError('检索结果标题与预期不符')
            filename = x.get('dataFile')
            position = x.get('offset')
            if not isinstance(filename, str) or not re.fullmatch('[A-Za-z0-9_]{1,60}', filename) or (not isinstance(position, str)) or (not re.fullmatch('[0-9]{1,20}', position)):
                raise RuntimeError('详情定位信息异常')
            r = s.get(BASE + 'minguofy/api/oldpage/minguo/', params={'datafile': filename, 'offset': position}, timeout=20)
            r.raise_for_status()
            content = r.content
    except requests.RequestException:
        raise RuntimeError('书同文请求失败') from None
    if len(content) > 2000000 or b'<!DOCTYPE' in content.upper() or b'<!ENTITY' in content.upper():
        raise RuntimeError('详情 XML 超限或包含不支持的声明')
    try:
        root = ET.fromstring(content)
    except ET.ParseError:
        raise RuntimeError('详情 XML 无法解析') from None
    if root.tag != 'artical':
        raise RuntimeError('详情根节点异常')
    titles = [''.join(x.itertext()).strip() for x in root if x.tag == 'para' and x.get('type') == '标题']
    if len(titles) != 1 or titles[0] != title:
        raise RuntimeError('详情标题与检索结果不符')
    paragraphs = []
    for x in root:
        if x.tag != 'para':
            raise RuntimeError('详情包含未识别节点')
        kind = x.get('type')
        align = x.get('align')
        if not isinstance(kind, str) or len(kind) > 30 or (align is not None and (len(align) > 30 or not re.fullmatch('[A-Za-z0-9_-]+', align))):
            raise RuntimeError('详情段落属性异常')
        paragraphs.append({'type_raw': kind, 'align_raw': align, 'text': None if kind == '图片' else ''.join(x.itertext())})
    return {'source': '书同文民国风云文献详情', 'account_marker': 'zjdx（书同文账户）', 'query': q, 'offset': offset, 'title': title, 'categories_raw': d['items'][0].get('categories'), 'paragraphs': paragraphs, 'note': '同一临时会话按检索结果重新定位并核对标题；段落依站方顺序与类型返回，图片仅保留占位不读取。书同文账户标记不证明此产品单独授权，来源完整性与正文使用范围须核对。'}
