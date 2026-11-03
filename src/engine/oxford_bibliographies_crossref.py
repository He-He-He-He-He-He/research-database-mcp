"""馆方试用所列的十五个学科 Oxford Bibliographies 公开词条元数据。"""
import release_runtime
import requests
from crossref_catalog_validation import validate_crossref_page
SUBJECTS = {'Anthropology': '9780199766567', 'International Relations': '9780199743292', 'Linguistics': '9780199772810', 'Sociology': '9780199756384', 'Philosophy': '9780195396577', 'Chinese Studies': '9780199920082', 'Management': '9780199846740', 'Psychology': '9780199828340', 'American Literature': '9780199827251', 'Literary and Critical Theory': '9780190221911', 'Medieval Studies': '9780195396584', 'Political Science': '9780199756223', 'Art History': '9780199920105', 'Renaissance and Reformation': '9780195399301', 'British and Irish Literature': '9780199846719'}
URL = 'https://api.crossref.org/works'

def oxford_bibliographies_metadata(query, subject, page=1, page_size=10, timeout=25):
    if not isinstance(query, str) or not query.strip() or len(query) > 200:
        raise ValueError('关键词须为 1–200 字')
    if subject not in SUBJECTS:
        raise ValueError('请选择 SUBJECTS 中的学科')
    if any((not isinstance(x, int) or isinstance(x, bool) for x in (page, page_size))) or page < 1 or (not 1 <= page_size <= 20):
        raise ValueError('页码须大于零，每页 1–20 条')
    if (page - 1) * page_size + page_size > 10000:
        raise ValueError('Crossref offset + rows must not exceed 10000')
    title = 'Oxford Bibliographies in ' + subject
    params = {'query.container-title': title, 'query.title': query.strip(), 'filter': 'prefix:10.1093,type:reference-entry', 'rows': page_size, 'offset': (page - 1) * page_size}
    r = requests.get(URL, params=params, timeout=timeout)
    r.raise_for_status()
    d = r.json().get('message', {})
    items = d.get('items')
    total = d.get('total-results')
    validate_crossref_page(d, page_size)
    prefix = '10.1093/obo/' + SUBJECTS[subject] + '-'
    rows = []
    for x in items:
        doi = x.get('DOI', '')
        titles = x.get('title', [])
        container = x.get('container-title', [])
        if not doi.lower().startswith(prefix) or title not in container or (not titles):
            continue
        rows.append({'doi': doi, 'title': titles[0], 'container_title': container, 'published': x.get('published', {}).get('date-parts'), 'url': x.get('URL')})
    return {'source': 'Crossref 公开参考词条元数据', 'source_url': URL, 'library_url': 'https://libdb.zju.edu.cn/s/lib/libtb/show/2097', 'query': query.strip(), 'subject': subject, 'page': page, 'upstream_total': total, 'items': rows, 'note': '覆盖馆方所列 15 个试用学科对应的 Crossref 旧式 DOI 前缀；Renaissance and Reformation 含宗教改革主题，馆方中文仅列文艺复兴；上游相关性检索后按学科 DOI 与资源名称过滤，可能空页或遗漏，包括其他 DOI 格式，上游总数不是筛选后的数量。馆方页面称试用至 2026-11-30；此公开题录不提供词条正文或验证机构试用权限。'}
