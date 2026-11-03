"""浙大馆方列出的 ASM 旧介绍示例期刊：Crossref 公开文章题录。"""
import release_runtime
import argparse, json, subprocess
from urllib.parse import urlencode
from crossref_catalog_validation import validate_crossref_page
JOURNALS = {'mcb': ('Molecular and Cellular Biology', '0270-7306'), 'aem': ('Applied and Environmental Microbiology', '0099-2240'), 'bacteriology': ('Journal of Bacteriology', '0021-9193'), 'virology': ('Journal of Virology', '0022-538X'), 'mmbr': ('Microbiology and Molecular Biology Reviews', '1092-2172'), 'cmr': ('Clinical Microbiology Reviews', '0893-8512'), 'aac': ('Antimicrobial Agents and Chemotherapy', '0066-4804'), 'cvi': ('Clinical Vaccine and Immunology', '1556-679X'), 'ec': ('Eukaryotic Cell', '1535-9786'), 'iai': ('Infection and Immunity', '0019-9567'), 'jcm': ('Journal of Clinical Microbiology', '0095-1137'), 'mbio': ('mBio', '2150-7511')}

def search(keyword, journal='aem', page=1, size=5):
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
        d = json.loads(p.stdout)['message']
        items = d['items']
        total = d['total-results']
    except (ValueError, KeyError, TypeError) as e:
        raise RuntimeError('Crossref 响应结构异常') from e
    validate_crossref_page(d, int(size))
    out = []
    for x in items:
        out.append({'title': (x.get('title') or [''])[0], 'authors': [' '.join([a.get('given', ''), a.get('family', '')]).strip() for a in x.get('author', [])], 'doi': x.get('DOI'), 'url': x.get('URL'), 'published': x.get('published', {}).get('date-parts'), 'journal': (x.get('container-title') or [title])[0]})
    return {'source': 'Crossref 公开题录', 'scope': '馆方页面所列 ASM 旧介绍列举的单一期刊文章元数据；不证明馆藏覆盖、机构身份或全文权限；Crossref 查询为相关性匹配', 'journal': title, 'issn': issn, 'keyword': keyword, 'page': int(page), 'size': int(size), 'total': total, 'items': out}
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('keyword')
    p.add_argument('--journal', choices=JOURNALS, default='aem')
    p.add_argument('--page', type=int, default=1)
    p.add_argument('--size', type=int, default=5)
    a = p.parse_args()
    print(json.dumps(search(a.keyword, a.journal, a.page, a.size), ensure_ascii=False, indent=2))
