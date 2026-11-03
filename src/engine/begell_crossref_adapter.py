"""Begell House Crossref 公开元数据，非出版社馆藏接口。"""
import release_runtime
import argparse
import json
import subprocess
from urllib.parse import urlencode
KINDS = {'journal': 'journal-article', 'proceedings': 'proceedings-article'}

def search(keyword, kind='journal', page=1, size=5):
    if kind not in KINDS or not isinstance(keyword, str) or (not keyword.strip()) or (not 1 <= int(page) <= 1000) or (not 1 <= int(size) <= 50):
        raise ValueError('请输入关键词、journal/proceedings、页码 1–1000 和每页 1–50 条')
    if (int(page) - 1) * int(size) + int(size) > 10000:
        raise ValueError('Crossref offset + rows must not exceed 10000')
    params = {'query': keyword, 'filter': 'type:' + KINDS[kind], 'rows': int(size), 'offset': (int(page) - 1) * int(size), 'select': 'DOI,title,author,published,container-title,URL,type'}
    url = 'https://api.crossref.org/members/613/works?' + urlencode(params)
    p = release_runtime.run(['curl', '--silent', '--show-error', '--fail', '--location', '--max-time', '25', url], capture_output=True, text=True, timeout=30)
    if p.returncode:
        raise RuntimeError('Crossref 题录请求失败: ' + p.stderr.strip())
    try:
        d = json.loads(p.stdout)['message']
        items = d['items']
        total = d['total-results']
        if not isinstance(items, list) or not isinstance(total, int):
            raise TypeError()
    except (ValueError, KeyError, TypeError) as e:
        raise RuntimeError('Crossref 响应结构异常') from e
    out = [{'title': (x.get('title') or [''])[0], 'authors': [' '.join((a.get('given', ''), a.get('family', ''))).strip() for a in x.get('author', [])], 'doi': x.get('DOI'), 'url': x.get('URL'), 'published': x.get('published', {}).get('date-parts'), 'container_title': (x.get('container-title') or [''])[0], 'type': x.get('type')} for x in items]
    return {'source': 'Crossref 公开题录，Begell House 会员 ID 613', 'library_info_url': 'https://libdb.zju.edu.cn/s/lib/libtb/show/985', 'scope': '按 Begell House Crossref 注册会员和文献类型筛选，不代表出版社数据库全部内容、学校订购范围、机构认证或全文权限；关键词按相关性检索。馆方资料注明期刊自 1982 年起；本检索未对年份作限制。', 'kind': kind, 'keyword': keyword, 'page': int(page), 'size': int(size), 'total': total, 'items': out}
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('keyword')
    p.add_argument('--kind', choices=KINDS, default='journal')
    p.add_argument('--page', type=int, default=1)
    p.add_argument('--size', type=int, default=5)
    a = p.parse_args()
    print(json.dumps(search(a.keyword, a.kind, a.page, a.size), ensure_ascii=False, indent=2))
