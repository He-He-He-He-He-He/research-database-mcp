"""浙大馆方列出的 馆方旧列 ECS 八种出版物：Crossref 公开文章题录。"""
import release_runtime
import argparse, json, subprocess
from urllib.parse import urlencode
from crossref_catalog_validation import validate_crossref_page
JOURNALS = {'jes': ('Journal of The Electrochemical Society', '1945-7111'), 'esl': ('Electrochemical and Solid-State Letters', '1944-8775'), 'meeting': ('ECS Meeting Abstracts', '2151-2043'), 'jss': ('ECS Journal of Solid State Science and Technology', '2162-8777'), 'ssl': ('ECS Solid State Letters', '2162-8750'), 'eel': ('ECS Electrochemistry Letters', '2162-8734'), 'interface': ('The Electrochemical Society Interface', '1944-8783'), 'transactions': ('ECS Transactions', '1938-5862')}
YEARS = {'jes': 1930, 'esl': 1998, 'meeting': 2002, 'jss': 2012, 'ssl': 2012, 'eel': 2012, 'interface': 1997, 'transactions': 2005}

def search(keyword, journal='jes', page=1, size=5):
    if journal not in JOURNALS or not isinstance(keyword, str) or (not keyword.strip()) or any((isinstance(x, bool) or not isinstance(x, (int, str)) or (isinstance(x, str) and (not x.isascii())) or (isinstance(x, str) and (not x.isdigit())) for x in (page, size))) or (not 1 <= int(page) <= 1000) or (not 1 <= int(size) <= 50):
        raise ValueError('请输入关键词、有效期刊、页码 1–1000 和每页 1–50 条')
    if (int(page) - 1) * int(size) + int(size) > 10000:
        raise ValueError('Crossref offset + rows must not exceed 10000')
    title, issn = JOURNALS[journal]
    params = {'query': keyword, 'filter': f'from-pub-date:{YEARS[journal]}-01-01,type:journal-article', 'rows': int(size), 'offset': (int(page) - 1) * int(size), 'select': 'DOI,title,author,published,container-title,URL,type,ISSN'}
    url = 'https://api.crossref.org/journals/' + issn + '/works?' + urlencode(params)
    p = release_runtime.run(['curl', '--silent', '--show-error', '--fail', '--location', '--max-time', '25', url], capture_output=True, text=True, timeout=30)
    if p.returncode:
        raise RuntimeError('Crossref 题录请求失败: ' + p.stderr.strip())
    try:
        d = json.loads(p.stdout)['message']
        items = d['items']
        total = d['total-results']
    except (ValueError, KeyError, TypeError) as e:
        raise RuntimeError('Crossref 响应结构异常') from e
    validate_crossref_page(d, int(size))
    out = []
    for x in items:
        out.append({'title': (x.get('title') or [''])[0], 'authors': [' '.join([a.get('given', ''), a.get('family', '')]).strip() for a in x.get('author', [])], 'doi': x.get('DOI'), 'url': x.get('URL'), 'published': x.get('published', {}).get('date-parts'), 'journal': (x.get('container-title') or [title])[0]})
    return {'source': 'Crossref 公开题录', 'scope': '馆方页面所列 馆方旧列 ECS 八种出版物之一的起始年份之后文章元数据；不证明馆藏覆盖、机构身份或全文权限；Crossref 查询为相关性匹配', 'journal': title, 'issn': issn, 'keyword': keyword, 'page': int(page), 'size': int(size), 'total': total, 'items': out}
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('keyword')
    p.add_argument('--journal', choices=JOURNALS, default='jes')
    p.add_argument('--page', type=int, default=1)
    p.add_argument('--size', type=int, default=5)
    a = p.parse_args()
    print(json.dumps(search(a.keyword, a.journal, a.page, a.size), ensure_ascii=False, indent=2))
