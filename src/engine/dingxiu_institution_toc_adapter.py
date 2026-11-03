"""鼎秀古籍浙大机构阅读器目录；不取正文或图片。"""
import release_runtime
import ast
import re
import requests
from bs4 import BeautifulSoup
from dingxiu_institution_catalog_adapter import BASE
from dingxiu_institution_page_adapter import READER

def toc(guid, expected_title, session=None):
    if not isinstance(guid, str) or not re.fullmatch('[A-Za-z0-9]{32}', guid):
        raise ValueError('图书 GUID 无效')
    if not isinstance(expected_title, str) or not expected_title.strip() or len(expected_title) > 200 or re.search('[\\x00-\\x1f]', expected_title):
        raise ValueError('须提供原站繁体书名')
    s = session or requests.Session()
    path = READER + guid + '/1/'
    try:
        r = s.get(BASE + 'index.do', timeout=20, allow_redirects=False)
        if r.status_code != 200:
            raise RuntimeError('机构页面不可用')
        p = BeautifulSoup(r.content, 'html.parser')
        inst = p.select_one('#nologin')
        if not inst or not re.search('机构\\s*[:：]\\s*浙江大学', inst.get_text(' ', strip=True)):
            raise RuntimeError('未确认浙江大学机构身份')
        r = s.get(path + 'index.do', timeout=25, allow_redirects=False)
        if r.status_code != 200:
            raise RuntimeError('阅读器不可用')
        p = BeautifulSoup(r.content, 'html.parser')
        b = p.select_one('#documentGuid')
        num = p.select_one('#initPageNum')
        total = p.select_one('#pageCount')
        title = p.select_one('.conttitleleft')
        if not b or b.get('value', '').lower() != guid.lower() or (not num) or (num.get('value') != '1') or (not total) or (not total.get('value', '').isdigit()) or (not title) or (title.get_text(' ', strip=True) != expected_title.strip()):
            raise RuntimeError('阅读器书号或标题不匹配')
        r = s.get(path + 'showToc.do', timeout=25, allow_redirects=False)
        if r.status_code != 200 or len(r.content) > 2000000:
            raise RuntimeError('目录响应不可用或超限')
        p = BeautifulSoup(r.content, 'html.parser')
        matches = []
        for node in p.select('script:not([src])'):
            matches.extend(re.findall('var\\s+treeNodes\\s*=\\s*(\\[[\\s\\S]*?\\]);', node.string or node.get_text()))
        if len(matches) != 1:
            raise RuntimeError('未识别站方目录')
        raw = ast.literal_eval(matches[0])
        if not isinstance(raw, list) or len(raw) > 10000:
            raise RuntimeError('目录结构异常')
        items = []
        for x in raw:
            if not isinstance(x, dict) or set(x) != {'id', 'parentId', 'name'} or any((not isinstance(x[k], str) for k in ('id', 'parentId', 'name'))) or (not x['id'].isdigit()) or (not x['parentId'].isdigit()) or (not x['name']) or re.search('https?://|(?:token|session|sid|clientuuid)\\s*=', x['name'], re.I):
                raise RuntimeError('目录节点异常')
            items.append({'id_raw': x['id'], 'parent_id_raw': x['parentId'], 'name': x['name']})
        return {'source': '鼎秀古籍机构阅读器目录', 'institution': '浙江大学', 'guid': guid, 'title': expected_title.strip(), 'reader_page_count': int(total['value']), 'items': items, 'note': '目录编号和父编号保留站方原值，其与印刷页码的关系未核；目录可见不代表逐页全文权限。未输出正文、图像或会话链接。'}
    except (requests.RequestException, ValueError, SyntaxError):
        raise RuntimeError('机构服务连接失败或目录响应无法解析') from None
