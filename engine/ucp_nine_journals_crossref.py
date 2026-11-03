"""浙大馆方所列九种 UCP 期刊的 Crossref 公开题录。"""
import release_runtime
import argparse
import json
import subprocess
from urllib.parse import urlencode
from crossref_catalog_validation import validate_crossref_page
JOURNALS = {'political-economy': ('Journal of Political Economy', '0022-3808'), 'law-economics': ('The Journal of Law and Economics', '0022-2186'), 'anthropology': ('Current Anthropology', '0011-3204'), 'historical-studies': ('Critical Historical Studies', '2326-4462'), 'modern-history': ('The Journal of Modern History', '0022-2801'), 'education': ('Comparative Education Review', '0010-4086'), 'library': ('The Library Quarterly', '0024-2519'), 'labor-economics': ('Journal of Labor Economics', '0734-306X'), 'sociology': ('American Journal of Sociology', '0002-9602')}

def search(keyword, journal='political-economy', page=1, size=5):
    if journal not in JOURNALS or not isinstance(keyword, str) or (not keyword.strip()) or any((isinstance(x, bool) or not isinstance(x, (int, str)) or (isinstance(x, str) and (not x.isascii())) or (isinstance(x, str) and (not x.isdigit())) for x in (page, size))) or (not 1 <= int(page) <= 1000) or (not 1 <= int(size) <= 50):
        raise ValueError('请输入关键词、有效期刊、页码 1–1000 和每页 1–50 条')
    if (int(page) - 1) * int(size) + int(size) > 10000:
        raise ValueError('Crossref offset + rows must not exceed 10000')
    title, issn = JOURNALS[journal]
    params = {'query': keyword, 'filter': 'type:journal-article', 'rows': int(size), 'offset': (int(page) - 1) * int(size), 'select': 'DOI,title,author,published,container-title,URL,type,ISSN'}
    url = 'https://api.crossref.org/journals/' + issn + '/works?' + urlencode(params)
    p = release_runtime.run(['curl', '--silent', '--show-error', '--fail', '--location', '--max-time', '25', url], capture_output=True, text=True, timeout=30)
    if p.returncode:
        raise RuntimeError('Crossref 题录请求失败: ' + p.stderr.strip())
    try:
        data = json.loads(p.stdout)['message']
        items = data['items']
        total = data['total-results']
        validate_crossref_page(data, int(size))
    except (ValueError, KeyError, TypeError) as exc:
        raise RuntimeError('Crossref 响应结构异常') from exc
    output = [{'title': (x.get('title') or [''])[0], 'authors': [' '.join((a.get('given', ''), a.get('family', ''))).strip() for a in x.get('author', [])], 'doi': x.get('DOI'), 'url': x.get('URL'), 'published': x.get('published', {}).get('date-parts'), 'journal': (x.get('container-title') or [title])[0]} for x in items]
    return {'source': 'Crossref 公开题录', 'library_info_url': 'https://libdb.zju.edu.cn/s/lib/libtb/show/1881', 'scope': '浙大馆方页面所列 9 刊之一的公开文章元数据；不代表馆藏订购年限、机构身份或全文权限。Crossref 关键词为相关性检索。', 'journal': title, 'issn': issn, 'keyword': keyword, 'page': int(page), 'size': int(size), 'total': total, 'items': output}
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('keyword')
    parser.add_argument('--journal', choices=JOURNALS, default='political-economy')
    parser.add_argument('--page', type=int, default=1)
    parser.add_argument('--size', type=int, default=5)
    args = parser.parse_args()
    print(json.dumps(search(args.keyword, args.journal, args.page, args.size), ensure_ascii=False, indent=2))
