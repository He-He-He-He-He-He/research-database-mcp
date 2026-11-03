"""中国金石总录试用库：全称模糊检索题录。"""
import release_runtime
import argparse, gzip, html, json, re
from urllib.request import Request, urlopen
URL = 'http://121.89.86.151:8000/api/v1/search/'

def search(keyword, page=1):
    if not keyword.strip():
        raise ValueError('关键词不能为空')
    if page < 1:
        raise ValueError('页码须大于零')
    payload = {'item_group': [], 'search_option': 'name', 'search_cate_option_id': 7, 'search_text': keyword, 'search_term': 'match', 'facet': {'cates_id': '', 'authors': '', 'dynasties': '', 'commonEra': '', 'fonts': ''}, 'page': page, 'pageSize': 20}
    req = Request(URL, data=json.dumps(payload, ensure_ascii=False).encode(), headers={'Content-Type': 'application/json'})
    with urlopen(req, timeout=25) as response:
        raw = response.read()
        raw = gzip.decompress(raw) if response.headers.get('Content-Encoding') == 'gzip' else raw
    result = json.loads(raw)
    data = result.get('datas')
    if not isinstance(data, dict) or not isinstance(data.get('list_datas'), list) or 'size' not in data:
        raise RuntimeError('服务未返回可识别结果')
    fields = ['id', 'info_id', 'alias', 'dynasty', 'author', 'font', 'material', 'chronology', 'excavation_site']
    items = []
    for row in data['list_datas']:
        entry = {k: row.get(k) for k in fields}
        entry['name'] = html.unescape(re.sub('<[^>]*>', '', row.get('name', '')))
        items.append(entry)
    return {'source': '中国金石总录试用库', 'scope': '试用库；馆方列校内 IP 试用至 2026-12-31', 'query': keyword, 'field': '全称模糊', 'page': page, 'total': data['size'], 'items': items, 'note': '上游使用未加密 HTTP，请勿提交敏感检索词；机构身份及全文和图像权限未验证。'}
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('keyword')
    p.add_argument('--page', type=int, default=1)
    a = p.parse_args()
    print(json.dumps(search(a.keyword, a.page), ensure_ascii=False, indent=2))
