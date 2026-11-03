"""书同文《东方杂志》总目期次检索，不读取正文。"""
import release_runtime
import re, requests
from urllib.parse import quote
from bs4 import BeautifulSoup
BASE = 'https://gujiku.unihan.com.cn/'

def search(keyword, offset=0, limit=10, include_sections=False):
    if not isinstance(keyword, str) or not 1 <= len(keyword.strip()) <= 80 or any((ord(c) < 32 for c in keyword)):
        raise ValueError('关键词须为1–80字单行文本')
    if type(offset) is not int or offset < 0 or type(limit) is not int or (not 1 <= limit <= 20):
        raise ValueError('offset 或 limit 无效')
    if type(include_sections) is not bool:
        raise ValueError('include_sections 须为布尔值')
    q = keyword.strip()
    try:
        with requests.Session() as s:
            r = s.get(BASE + 'Products/Search/QSL', timeout=20)
            r.raise_for_status()
            if 'zjdx' not in BeautifulSoup(r.content, 'html.parser').get_text(' ', strip=True):
                raise RuntimeError('未确认书同文学校账户标记')
            r = s.get(BASE + 'minguofy/api/oldcatalog/search/MinGuoFY/' + quote(q, safe=''), timeout=20)
            r.raise_for_status()
            d = r.json()
            ids = d.get('ids') if isinstance(d, dict) else None
            if not isinstance(ids, list) or any((not isinstance(x, str) or not re.fullmatch('c[0-9]+', x) for x in ids)) or len(set(ids)) != len(ids):
                raise RuntimeError('期次检索结果异常')
            r = s.get(BASE + 'minguofy/api/catalog/get/MinGuoFY', params={'id': 'root'}, timeout=20)
            r.raise_for_status()
            root = r.json()
            if not isinstance(root, list):
                raise RuntimeError('期次目录异常')
            byid = {}
            for x in root:
                if not isinstance(x, dict) or not isinstance(x.get('id'), str) or (not re.fullmatch('c[0-9]+', x['id'])) or (not isinstance(x.get('text'), str)) or (x['id'] in byid):
                    raise RuntimeError('期次目录字段异常')
                byid[x['id']] = x['text']
            if any((re.search('(?i)(?:https?://|(?:token|session|sid|apikey)\\s*=)', v) for v in byid.values())):
                raise RuntimeError('期次字段包含异常链接或凭据')
            if any((i not in byid for i in ids)):
                raise RuntimeError('搜索期次不在原站目录')
            wanted = set(ids)
            ordered = [i for i in byid if i in wanted]
            selected = ordered[offset:offset + limit]
            sections = {}
            if include_sections and selected:
                r = s.get(BASE + 'minguofy/api/catalog/get/MinGuoFY', params={'id': ','.join(selected)}, timeout=20)
                r.raise_for_status()
                raw = r.json()
                if len(selected) == 1 and isinstance(raw, list):
                    raw = {selected[0]: raw}
                if not isinstance(raw, dict) or set(raw) != set(selected):
                    raise RuntimeError('栏目期次对应异常')
                for i in selected:
                    if not isinstance(raw[i], list) or any((not isinstance(x, dict) or not isinstance(x.get('text'), str) for x in raw[i])):
                        raise RuntimeError('栏目结构异常')
                    sections[i] = [x['text'] for x in raw[i]]
                    if any((re.search('(?i)(?:https?://|(?:token|session|sid|apikey)\\s*=)', v) for v in sections[i])):
                        raise RuntimeError('栏目字段包含异常链接或凭据')
    except requests.RequestException:
        raise RuntimeError('书同文请求失败') from None
    items = [{'id': i, 'issue_raw': byid[i], **({'all_sections_raw': sections[i]} if include_sections else {})} for i in selected]
    return {'source': '书同文《东方杂志》总目', 'account_marker': 'zjdx（书同文账户）', 'query': q, 'total_issues': len(ids), 'offset': offset, 'limit': limit, 'next_offset': offset + limit if offset + limit < len(ids) else None, 'items': items, 'note': '按站方原始期次顺序本地分页；若请求栏目，返回每个命中期次的全部栏目，不代表每个栏目均匹配关键词。仅总目，学校账户标记不证明此产品授权或文章全文权限。'}
