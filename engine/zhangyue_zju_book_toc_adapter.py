"""掌阅浙江大学图书馆频道公开书目目录，不读取正文。"""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
from zhangyue_zju_catalog_adapter import BASE, APP

def toc(book_id, expected_title, page=1, limit=50, session=None):
    if not isinstance(book_id, str) or not re.fullmatch('[0-9]{1,20}', book_id):
        raise ValueError('书号须为数字')
    if not isinstance(expected_title, str) or not expected_title.strip() or len(expected_title) > 200 or re.search('[\\x00-\\x1f]', expected_title):
        raise ValueError('须提供完整书名')
    if type(page) is not int or not 1 <= page <= 100:
        raise ValueError('page 须为 1–100')
    if type(limit) is not int or not 1 <= limit <= 50:
        raise ValueError('limit 须为 1–50')
    s = session or requests.Session()
    try:
        r = s.get(BASE + 'book/detail', params={'appId': APP, 'bookType': '1', 'bookId': book_id}, timeout=25, allow_redirects=False)
        if r.status_code != 200:
            raise RuntimeError('书目详情不可用')
        p = BeautifulSoup(r.content, 'html.parser')
        names = p.select('.book_name')
        echoes = re.findall('(?i)\\bbookid\\s*[:=]\\s*["\\\']([0-9]+)["\\\']', r.text)
        if not p.title or p.title.get_text(strip=True) != '浙江大学图书馆' or (not names) or (names[0].get_text(' ', strip=True) != expected_title.strip()) or (echoes != [book_id]):
            raise RuntimeError('频道、书号或书名未确认')
        tabs = [x.get_text(' ', strip=True) for x in p.select('.tab_item')]
        matches = [re.search('目录[（(]共\\s*([0-9,]+)\\s*章[）)]', x) for x in tabs]
        matches = [x for x in matches if x]
        if len(matches) != 1:
            raise RuntimeError('原站目录总数未确认')
        total = int(matches[0].group(1).replace(',', ''))
        max_page = max(1, (total + 49) // 50)
        if page > max_page:
            raise ValueError('请求页超出站方目录范围')
        initial = p.select('.catalog_wrap .chapter_list > li')
        if len(initial) != min(50, total):
            raise RuntimeError('站方目录首页数量异常')
        items = []
        if page == 1:
            for index, node in enumerate(initial, 1):
                m = re.fullmatch('\\s*([0-9]+)\\.\\s*(\\S[\\s\\S]*)', node.get_text(' ', strip=True))
                if not m or int(m.group(1)) != index:
                    raise RuntimeError('首页目录编号异常')
                if re.search('[a-z][a-z0-9+.-]*://|www\\.|(?:href|src)\\s*=|(?:token|session|sid|apikey|api_key)\\s*=', m.group(2), re.I):
                    raise RuntimeError('目录标题包含链接或敏感参数')
                items.append({'number_raw': int(m.group(1)), 'title': m.group(2)})
        else:
            r = s.get(BASE + 'book/chapter', params={'appId': APP, 'bookType': '1', 'bookId': book_id, 'page': page}, timeout=25, allow_redirects=False)
            if r.status_code != 200:
                raise RuntimeError('后续目录页不可用')
            j = r.json()
            body = j.get('body') if isinstance(j, dict) and j.get('code') == 0 else None
            pager = body.get('pager') if isinstance(body, dict) else None
            rows = body.get('data') if isinstance(body, dict) else None
            if not isinstance(pager, dict) or pager.get('page') != page or pager.get('pageSize') != 50 or (pager.get('total') != total) or (pager.get('totalPage') != max_page) or (not isinstance(rows, list)) or (len(rows) != min(50, max(0, total - (page - 1) * 50))):
                raise RuntimeError('后续目录分页或数量异常')
            for index, x in enumerate(rows, (page - 1) * 50 + 1):
                if not isinstance(x, dict) or type(x.get('id')) is not int or x['id'] != index or (not isinstance(x.get('chapterName'), str)) or (not x['chapterName'].strip()):
                    raise RuntimeError('目录条目异常')
                if re.search('[a-z][a-z0-9+.-]*://|www\\.|(?:href|src)\\s*=|(?:token|session|sid|apikey|api_key)\\s*=', x['chapterName'], re.I):
                    raise RuntimeError('目录标题包含链接或敏感参数')
                items.append({'number_raw': x['id'], 'title': x['chapterName']})
        return {'source': '掌阅精选浙江大学图书馆频道公开书目目录', 'book_id': book_id, 'title': expected_title.strip(), 'page': page, 'source_page_size': 50, 'declared_total_raw': total, 'source_page_items': len(items), 'page_truncated': len(items) > limit, 'has_more_pages': page < max_page, 'items': items[:limit], 'note': '频道名不证明当前机构认证或逐章阅读权限。源页最多 50 条；本地截断的余项不会进入下一页。后续页响应未回显书号，已在同一会话核对首页书号及书名和后续分页；不输出阅读链接或正文。'}
    except requests.RequestException:
        raise RuntimeError('掌阅服务连接失败') from None
