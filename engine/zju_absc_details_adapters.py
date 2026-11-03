"""浙大古籍特藏：定位公开状态条目及读取单条书目。"""
import release_runtime
import argparse, json, re, uuid
from http.cookiejar import CookieJar
from urllib.request import Request, build_opener, HTTPCookieProcessor, urlopen
from bs4 import BeautifulSoup
from zju_absc_api import BASE
from zju_absc_page_counts import _validate_page

def public_search(keyword, page=1):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100:
        raise ValueError('请输入1–100字关键词')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 500):
        raise ValueError('页码须为1–500')
    op = build_opener(HTTPCookieProcessor(CookieJar()))
    with op.open(BASE + 'document/search-page', timeout=20) as r:
        html = r.read().decode('utf-8')
    m = re.search('name="csrf-token" content="([^"]+)', html)
    if not m:
        raise RuntimeError('无法取得检索会话')
    p = {'draw': 1, 'order': [], 'page_size': 20, 'page_index': (page - 1) * 20, 'search_text': keyword.strip(), 'classification': [], 'document_type': [], 'responsible_people': []}
    req = Request(BASE + 'document/get-list', data=json.dumps(p, ensure_ascii=False).encode(), headers={'Content-Type': 'application/json', 'X-CSRFToken': m.group(1)})
    with op.open(req, timeout=25) as r:
        data = json.load(r)
    _validate_page(data, page)
    items = [{'id': x.get('id'), 'title': x.get('title'), 'responsible_people': x.get('responsible_people'), 'copyright_type': x.get('copyright_type'), 'copyright_type_name': x.get('copyright_type_name')} for x in data['data'] if x.get('copyright_type') == 'public']
    return {'source': '浙江大学古籍特藏发布平台', 'query': keyword.strip(), 'page': page, 'total_all_types': data['total_count'], 'items': items, 'note': '仅筛本页 public 记录；非全库公开资源数量，其他权限类型未处理。HTTP 明文。'}

def public_detail(keyword, page, record_id):
    try:
        if not isinstance(record_id, str) or str(uuid.UUID(record_id)) != record_id.lower():
            raise ValueError()
    except (ValueError, AttributeError):
        raise ValueError('需要规范 UUID')
    record_id = record_id.lower()
    candidates = public_search(keyword, page)['items']
    matching = [x for x in candidates if x['id'] == record_id]
    if len(matching) != 1:
        raise ValueError('该检索页未识别唯一的 public 条目')
    url = BASE + 'document/info/' + record_id + '/public'
    with urlopen(url, timeout=20) as r:
        html = r.read().decode('utf-8')
    s = BeautifulSoup(html, 'html.parser')
    t = s.select_one('table#document-info')
    if not t:
        raise RuntimeError('未识别记录详情或无权限')
    fields = []
    for row in t.select(':scope > tbody > tr, :scope > tr'):
        th = row.find('th', recursive=False)
        td = row.find('td', recursive=False)
        if th and td:
            label = th.get_text(' ', strip=True).rstrip(':：')
            if label not in ('全文地址', '附件', '所属專題'):
                fields.append({'label': label, 'value': td.get_text(' ', strip=True)})
    if not any((x['label'] in ('題名', '題名卷數') and x['value'] == matching[0]['title'] for x in fields)):
        raise RuntimeError('详情题名与公开检索条目不符')
    return {'source': '浙大古籍特藏公开书目详情', 'record_url': url, 'fields': fields, 'note': '仅提取 public 书目字段；不获取全文、图片、附件。公开标记不等于任意内容复用许可。HTTP 明文。'}
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    sp = p.add_subparsers(dest='cmd', required=True)
    x = sp.add_parser('search')
    x.add_argument('keyword')
    x.add_argument('--page', type=int, default=1)
    x = sp.add_parser('detail')
    x.add_argument('keyword')
    x.add_argument('id')
    x.add_argument('--page', type=int, default=1)
    a = p.parse_args()
    print(json.dumps(public_search(a.keyword, a.page) if a.cmd == 'search' else public_detail(a.keyword, a.page, a.id), ensure_ascii=False, indent=2))
