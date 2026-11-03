"""文心阁浙大 IP 阅读器目录，不保存会话参数。"""
import release_runtime
import ast
import re
import requests
from bs4 import BeautifulSoup
from wenxinge_institution_catalog_adapter import BASE

def toc(book_id, reader_title, session=None):
    if not isinstance(book_id, str) or not re.fullmatch('[A-Za-z0-9]{32}', book_id):
        raise ValueError('阅读器书号无效')
    if not isinstance(reader_title, str) or not reader_title.strip() or len(reader_title) > 200 or re.search('[\\x00-\\x1f]', reader_title):
        raise ValueError('须提供阅读器显示的完整书名')
    s = session or requests.Session()
    path = 'home/readPage/' + book_id + '/1/'
    try:
        r = s.get(BASE + 'home/doc/index.do', timeout=20, allow_redirects=False)
        if r.status_code != 200:
            raise RuntimeError('机构页面不可用')
        p = BeautifulSoup(r.content, 'html.parser')
        if '浙江大学' not in p.get_text(' ', strip=True):
            raise RuntimeError('未确认浙江大学机构身份')
        flag = p.select_one('#ytzFlag')
        if not flag or not flag.get('value'):
            raise RuntimeError('缺少阅读器参数')
        r = s.get(BASE + path + 'index.do', params={'ytzFlag': flag['value']}, timeout=25, allow_redirects=False)
        if r.status_code != 200:
            raise RuntimeError('阅读器不可用')
        p = BeautifulSoup(r.content, 'html.parser')

        def value(k):
            x = p.select_one('#' + k)
            return x.get('value') if x else None
        total = value('pageCount')
        if value('documentGuid') != book_id or value('initPageNum') != '1' or value('documentName') != reader_title.strip() or (not total) or (not total.isdigit()):
            raise RuntimeError('阅读器编号或书名不匹配')
        r = s.get(BASE + path + 'showToc.do', timeout=25, allow_redirects=False)
        if r.status_code != 200 or len(r.content) > 2000000:
            raise RuntimeError('目录响应不可用或超限')
        p = BeautifulSoup(r.content, 'html.parser')
        matches = []
        for node in p.select('script:not([src])'):
            text = node.string or node.get_text()
            matches.extend(re.findall('var\\s+treeNodes\\s*=\\s*(\\[[\\s\\S]*?\\]);', text))
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
        return {'source': '文心阁机构阅读器目录', 'institution': '浙江大学', 'book_id': book_id, 'reader_title': reader_title.strip(), 'reader_page_count': int(total), 'items': items, 'note': '目录节点 id 与 parentId 保留站方原值，其与印刷页码的对应关系未核；阅读器书名可能与检索书目异体字不同。目录可见不代表各章全文权限；不输出会话参数和正文。'}
    except (requests.RequestException, ValueError, SyntaxError):
        raise RuntimeError('机构服务连接失败或目录响应无法解析') from None
