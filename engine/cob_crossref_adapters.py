"""Crossref 中的浙大馆方列示 COB 五刊公开题录；不代表全文授权。"""
import release_runtime
import json, subprocess
from urllib.parse import urlencode
JOURNALS = {'development': ('Development', '1477-9129'), 'cell_science': ('Journal of Cell Science', '1477-9137'), 'experimental_biology': ('The Journal of Experimental Biology', '1477-9145'), 'disease_models': ('Disease Models & Mechanisms', '1754-8403'), 'biology_open': ('Biology Open', '2046-6390')}

def search(keyword, journal='development', page=1, rows=5):
    if not keyword.strip() or journal not in JOURNALS or (not 1 <= int(page) <= 1000) or (not 1 <= int(rows) <= 20):
        raise ValueError('关键词、期刊、页码或数量无效')
    if (int(page) - 1) * int(rows) + int(rows) > 10000:
        raise ValueError('Crossref offset + rows must not exceed 10000')

    def one(key):
        title, issn = JOURNALS[key]
        url = 'https://api.crossref.org/journals/' + issn + '/works?' + urlencode({'query.bibliographic': keyword, 'rows': int(rows), 'offset': (int(page) - 1) * int(rows)})
        p = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--location', '--max-time', '30', url], capture_output=True, text=True, timeout=35)
        if p.returncode:
            raise RuntimeError(title + ' 查询失败: ' + p.stderr.strip())
        try:
            data = json.loads(p.stdout)
            msg = data['message']
            assert data['status'] == 'ok' and isinstance(msg['items'], list)
            items = [{'title': (x.get('title') or [''])[0], 'doi': x.get('DOI'), 'url': x.get('URL'), 'published': x.get('published'), 'authors': [{'given': a.get('given'), 'family': a.get('family')} for a in x.get('author', [])]} for x in msg['items']]
            return {'journal': title, 'issn': issn, 'total': msg.get('total-results'), 'items': items}
        except (ValueError, KeyError, TypeError, AssertionError) as exc:
            raise RuntimeError(title + ' 响应结构异常') from exc
    results = [one(journal)]
    return {'source': 'Crossref；按浙大图书馆所列 Company of Biologists 五刊在线 ISSN 限定', 'keyword': keyword, 'page': int(page), 'per_journal': int(rows), 'journals': results, 'scope': '公开元数据，相关性检索；不是出版社平台检索，机构识别及全文权限未验证'}
if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('keyword')
    p.add_argument('--journal', choices=list(JOURNALS), default='development')
    p.add_argument('--page', type=int, default=1)
    p.add_argument('--rows', type=int, default=5)
    a = p.parse_args()
    print(json.dumps(search(a.keyword, a.journal, a.page, a.rows), ensure_ascii=False, indent=2))
