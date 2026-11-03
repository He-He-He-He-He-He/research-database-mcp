"""浙大馆方列出的 APS 14 种期刊：Crossref 公开文章题录。"""
import release_runtime
import argparse, json, subprocess
from urllib.parse import urlencode
from crossref_catalog_validation import validate_crossref_page
JOURNALS = {'cell': ('American Journal of Physiology-Cell Physiology', '0363-6143'), 'endocrine': ('American Journal of Physiology-Endocrinology and Metabolism', '0193-1849'), 'gastro': ('American Journal of Physiology-Gastrointestinal and Liver Physiology', '0193-1857'), 'heart': ('American Journal of Physiology-Heart and Circulatory Physiology', '0363-6135'), 'lung': ('American Journal of Physiology-Lung Cellular and Molecular Physiology', '1040-0605'), 'regulatory': ('American Journal of Physiology-Regulatory, Integrative and Comparative Physiology', '0363-6119'), 'renal': ('American Journal of Physiology-Renal Physiology', '1522-1466'), 'applied': ('Journal of Applied Physiology', '8750-7587'), 'neuro': ('Journal of Neurophysiology', '0022-3077'), 'genomics': ('Physiological Genomics', '1094-8341'), 'reviews': ('Physiological Reviews', '0031-9333'), 'physiology': ('Physiology', '1548-9213'), 'education': ('Advances in Physiology Education', '1043-4046'), 'reports': ('Physiological Reports', '2051-817X')}

def search(keyword, journal='cell', page=1, size=5):
    if journal not in JOURNALS or not isinstance(keyword, str) or (not keyword.strip()) or any((isinstance(x, bool) or not isinstance(x, (int, str)) or (isinstance(x, str) and (not x.isascii())) or (isinstance(x, str) and (not x.isdigit())) for x in (page, size))) or (not 1 <= int(page) <= 1000) or (not 1 <= int(size) <= 50):
        raise ValueError('请输入关键词、有效期刊、页码 1–1000 和每页 1–50 条')
    if (int(page) - 1) * int(size) + int(size) > 10000:
        raise ValueError('Crossref offset + rows must not exceed 10000')
    title, issn = JOURNALS[journal]
    params = {'query': keyword, 'filter': 'from-pub-date:1998-01-01,type:journal-article', 'rows': int(size), 'offset': (int(page) - 1) * int(size), 'select': 'DOI,title,author,published,container-title,URL,type,ISSN'}
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
    return {'source': 'Crossref 公开题录', 'scope': '馆方页面所列 APS 14 刊之一的 1998 年起文章元数据；不证明馆藏覆盖、机构身份或全文权限；Crossref 查询为相关性匹配', 'journal': title, 'issn': issn, 'keyword': keyword, 'page': int(page), 'size': int(size), 'total': total, 'items': out}
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('keyword')
    p.add_argument('--journal', choices=JOURNALS, default='cell')
    p.add_argument('--page', type=int, default=1)
    p.add_argument('--size', type=int, default=5)
    a = p.parse_args()
    print(json.dumps(search(a.keyword, a.journal, a.page, a.size), ensure_ascii=False, indent=2))
