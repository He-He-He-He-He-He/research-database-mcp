"""中国国家图书馆实体馆藏查询平台公开书目检索。"""
import release_runtime
import json
import subprocess
from urllib.parse import quote
BASE = 'https://meta.nlc.cn'
FIELDS = {'ANY', 'TIT', 'ISB', 'UBN', 'AUT', 'PUB', 'SUB', 'CLC', 'YEA', 'SET'}
NOTE = '原站年份、作者等字段可能为多值数组，不可将某一项自动认定为唯一出版年或唯一作者；须核对书目原文。'

def search(keyword, field='TIT', page=1, exact=False):
    if not isinstance(keyword, str) or not keyword.strip() or field not in FIELDS or isinstance(page, bool) or (not (isinstance(page, int) or (isinstance(page, str) and page.isascii() and page.isdigit()))) or (not 1 <= int(page) <= 10) or (not isinstance(exact, bool)):
        raise ValueError('请提供关键词、有效字段、整数页码及布尔精确匹配选项（网站前台限制前 100 条）')
    body = {'q': keyword, 'searchWay': field, 'query': keyword if field == 'ANY' else field + '=' + keyword, 'page_num': str(page), 'sort': [{'_score': 'DESC'}], 'size': 10, 'facetVal': [], 'exactMatch': exact}
    p = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--location', '--max-time', '35', '--data-binary', json.dumps(body, ensure_ascii=False), BASE + '/v2/doSearch?hight=false'], capture_output=True, text=True, timeout=40)
    if p.returncode:
        raise RuntimeError('国图目录查询失败: ' + p.stderr.strip())
    try:
        response = json.loads(p.stdout)
    except ValueError as exc:
        raise RuntimeError('国图响应不是 JSON，可能站点已变化') from exc
    if response.get('status') in (1, '1') and response.get('message') == 'no matching result':
        return {'source': '中国国家图书馆实体馆藏查询平台', 'keyword': keyword, 'field': field, 'page': int(page), 'total': 0, 'items': [], 'note': NOTE}
    if response.get('status') != 0 or not isinstance(response.get('result'), list):
        raise RuntimeError('国图查询出错: ' + str(response.get('message', '未知响应')))
    items = []
    for item in response['result']:
        src = item.get('_source', {})
        uid = str(item.get('_id', ''))
        items.append({'id': uid, 'title': src.get('TIT'), 'authors': src.get('AUT'), 'publisher': src.get('PUB'), 'year': src.get('YEA'), 'isbn': src.get('ISB'), 'subjects': src.get('SUB'), 'holdings': src.get('holdings'), 'detail_url': BASE + '/v2/detail/' + quote(uid, safe='')})
    return {'source': '中国国家图书馆实体馆藏查询平台', 'keyword': keyword, 'field': field, 'page': int(page), 'total': response.get('total'), 'items': items, 'note': NOTE}
if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('keyword')
    p.add_argument('--field', choices=sorted(FIELDS), default='TIT')
    p.add_argument('--page', type=int, default=1)
    p.add_argument('--exact', action='store_true')
    a = p.parse_args()
    print(json.dumps(search(a.keyword, a.field, a.page, a.exact), ensure_ascii=False, indent=2))
