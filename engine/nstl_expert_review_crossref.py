"""浙大馆方医药页列出的16 种 NSTL Expert Review 期刊公开题录。"""
import release_runtime
import requests
JOURNALS = {'Expert Review of Anticancer Therapy': '1473-7140', 'Expert Review of Anti-infective Therapy': '1478-7210', 'Expert Review of Cardiovascular Therapy': '1477-9072', 'Expert Review of Clinical Immunology': '1744-666X', 'Expert Review of Ophthalmology': '1746-9899', 'Expert Review of Respiratory Medicine': '1747-6348', 'Expert Review of Clinical Pharmacology': '1751-2433', 'Expert Review of Endocrinology & Metabolism': '1744-6651', 'Expert Review of Gastroenterology & Hepatology': '1747-4124', 'Expert Review of Hematology': '1747-4086', 'Expert Review of Medical Devices': '1743-4440', 'Expert Review of Molecular Diagnostics': '1473-7159', 'Expert Review of Neurotherapeutics': '1473-7175', 'Expert Review of Pharmacoeconomics & Outcomes Research': '1473-7167', 'Expert Review of Proteomics': '1478-9450', 'Expert Review of Vaccines': '1476-0584'}

def expert_review_metadata(query, journal, page=1, page_size=10, timeout=25):
    if not isinstance(query, str) or not query.strip() or len(query) > 200:
        raise ValueError('关键词须为 1–200 字')
    if journal not in JOURNALS:
        raise ValueError('请选择 JOURNALS 中的期刊全称')
    if any((not isinstance(x, int) or isinstance(x, bool) for x in (page, page_size))) or page < 1 or (not 1 <= page_size <= 20):
        raise ValueError('页码须大于零，每页 1–20 条')
    if (page - 1) * page_size + page_size > 10000:
        raise ValueError('Crossref offset + rows must not exceed 10000')
    issn = JOURNALS[journal]
    url = f'https://api.crossref.org/journals/{issn}/works'
    r = requests.get(url, params={'query': query.strip(), 'filter': 'type:journal-article', 'rows': page_size, 'offset': (page - 1) * page_size}, timeout=timeout)
    r.raise_for_status()
    d = r.json().get('message', {})
    items = d.get('items')
    total = d.get('total-results')
    if not isinstance(items, list) or not isinstance(total, int):
        raise ValueError('Crossref 返回结构异常')
    rows = [{'doi': x.get('DOI'), 'title': x['title'][0], 'journal': x.get('container-title', []), 'published': x.get('published', {}).get('date-parts'), 'url': x.get('URL')} for x in items if x.get('title')]
    return {'source': 'Crossref 公开期刊题录', 'source_url': url, 'library_url': 'https://libdb.zju.edu.cn/s/lib/libtb/show/1227', 'query': query.strip(), 'journal': journal, 'issn': issn, 'page': page, 'upstream_total': total, 'items': rows, 'note': '仅馆方页面列出的 16 种 Expert Review 期刊，非 NSTL 全库。馆方说明 NSTL 为全国学术性、非营利科研及教学机构开通访问；公开元数据不能证明当前具体全文权限或订购年限。Crossref 收录和关键词匹配可能不完整。'}
