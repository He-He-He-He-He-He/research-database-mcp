"""CNRDS 校园 IP 正常学校登录后的目录候选查询，临时会话不保存。"""
import release_runtime
import requests
from bs4 import BeautifulSoup
BASE = 'https://www.cnrds.com'

def search(keyword, limit=10, *, offset=0):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100 or any((c in keyword for c in '\r\n')):
        raise ValueError('关键词须为1–100字单行文本')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 10) or (type(offset) is not int) or (not 0 <= offset <= 10000):
        raise ValueError('limit 须为1–10')
    with requests.Session() as session:
        session.trust_env = True
        r = session.get(BASE + '/Home/Index', timeout=20)
        r.raise_for_status()
        token = BeautifulSoup(r.text, 'html.parser').select_one('input[name="__RequestVerificationToken"]')
        if not token or not token.get('value'):
            raise RuntimeError('未识别学校登录表单；页面或会话可能变化')
        payload = {'__RequestVerificationToken': token['value'], 'username': '', 'password': '', 'loginType': 'byPassword', 'anonymous': 'false', 'school': 'true'}
        r = session.post(BASE + '/Home/Login', data=payload, timeout=20)
        r.raise_for_status()
        r = session.get(BASE + '/Home/SearchNew', params={'text': keyword.strip(), 'opt': 'all'}, timeout=20)
        r.raise_for_status()
        if 'application/json' not in r.headers.get('Content-Type', '').lower():
            raise RuntimeError('目录未返回 JSON，请检查学校登录或授权状态')
        try:
            rows = r.json()
        except ValueError:
            raise RuntimeError('目录返回非 JSON') from None
        if not isinstance(rows, list):
            raise RuntimeError('目录响应结构异常')
        items = []
        for row in rows:
            if not isinstance(row, dict) or not isinstance(row.get('DisplayName'), str) or (row.get('ViewName') is not None and (not isinstance(row.get('ViewName'), str))) or (not isinstance(row.get('DB'), str)):
                raise RuntimeError('目录条目缺少必要字段')
            items.append({k: row.get(k) for k in ('DisplayName', 'ViewName', 'DB', 'Module')})
        return {'source': 'CNRDS 中国研究数据服务平台目录', 'query': keyword.strip(), 'returned_candidates': len(items), 'offset': offset, 'limit': limit, 'next_offset': offset + limit if offset + limit < len(items) else None, 'items': items[offset:offset + limit], 'note': '校园网络通过网站学校登录表单取得临时会话后的目录候选，不保存凭据；此次响应未明确标示浙江大学，具体数据库权限、数据数值与下载未验证；ViewName 可能由源站省略，保留为空；每次获取当前候选后本地截取，跨请求源顺序可能变化；返回数为本次候选数，不代表全库规模。'}
