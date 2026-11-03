"""浙江大学古籍特藏平台：公开题录检索。"""
import release_runtime
import argparse, json, re
from http.cookiejar import CookieJar
from urllib.request import Request, build_opener, HTTPCookieProcessor
from zju_absc_page_counts import _validate_page
BASE = 'http://absc.zju.edu.cn/'

def search(keyword, page=1):
    if not isinstance(keyword, str) or not keyword.strip():
        raise ValueError('关键词不能为空')
    if isinstance(page, bool) or not isinstance(page, int) or page < 1:
        raise ValueError('页码须为正整数')
    op = build_opener(HTTPCookieProcessor(CookieJar()))
    with op.open(BASE + 'document/search-page', timeout=20) as r:
        html = r.read().decode('utf-8')
    match = re.search('name="csrf-token" content="([^"]+)', html)
    if not match:
        raise RuntimeError('未取得页面检索会话，可能服务状态已改变')
    payload = {'draw': 1, 'order': [], 'page_size': 20, 'page_index': (page - 1) * 20, 'search_text': keyword, 'classification': [], 'document_type': [], 'responsible_people': []}
    req = Request(BASE + 'document/get-list', data=json.dumps(payload, ensure_ascii=False).encode(), headers={'Content-Type': 'application/json', 'X-CSRFToken': match.group(1)})
    with op.open(req, timeout=25) as r:
        result = json.load(r)
    _validate_page(result, page)
    fields = ['id', 'title', 'responsible_people', 'publisher', 'organization_name', 'resource_type_name', 'copyright_type_name', 'call_number']
    items = [{k: item.get(k) for k in fields} for item in result['data']]
    return {'source': '浙江大学古籍特藏发布平台', 'query': keyword, 'page': page, 'total': result['total_count'], 'items': items, 'note': '上游使用未加密 HTTP，请勿提交敏感检索词；公开状态不代表全文权限。'}
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('keyword')
    p.add_argument('--page', type=int, default=1)
    a = p.parse_args()
    print(json.dumps(search(a.keyword, a.page), ensure_ascii=False, indent=2))
