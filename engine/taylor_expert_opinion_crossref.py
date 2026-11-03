"""馆方列出的 Expert Opinion 十一种期刊，Crossref 公开元数据。"""
import release_runtime
import requests
JOURNALS = {'Expert Opinion on Biological Therapy': '1471-2598', 'Expert Opinion on Drug Delivery': '1742-5247', 'Expert Opinion on Drug Discovery': '1746-0441', 'Expert Opinion on Drug Metabolism & Toxicology': '1742-5255', 'Expert Opinion on Drug Safety': '1474-0338', 'Expert Opinion on Emerging Drugs': '1472-8214', 'Expert Opinion on Investigational Drugs': '1354-3784', 'Expert Opinion on Orphan Drugs': '2167-8707', 'Expert Opinion on Pharmacotherapy': '1465-6566', 'Expert Opinion on Therapeutic Patents': '1354-3776', 'Expert Opinion on Therapeutic Targets': '1472-8222'}

def expert_opinion_metadata(query, journal, page=1, page_size=10, timeout=25):
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
    r = requests.get(url, params={'query': query.strip(), 'filter': 'from-pub-date:1997-01-01,type:journal-article', 'rows': page_size, 'offset': (page - 1) * page_size}, timeout=timeout)
    r.raise_for_status()
    d = r.json().get('message', {})
    items = d.get('items')
    total = d.get('total-results')
    if not isinstance(items, list) or not isinstance(total, int):
        raise ValueError('Crossref 返回结构异常')
    rows = []
    for x in items:
        titles = x.get('title', [])
        if not titles:
            continue
        rows.append({'doi': x.get('DOI'), 'title': titles[0], 'journal': x.get('container-title', []), 'published': x.get('published', {}).get('date-parts'), 'url': x.get('URL')})
    return {'source': 'Crossref 公开期刊题录', 'source_url': url, 'library_url': 'https://libdb.zju.edu.cn/s/lib/libtb/show/1227', 'query': query.strip(), 'journal': journal, 'issn': issn, 'page': page, 'upstream_total': total, 'items': rows, 'note': '限定馆方页面列出的 11 个具体刊名之一及 1997 年以后公开元数据，非完整医药库。馆方介绍称该系列 10 种但实际列出 11 项，本接口保留全部 11 项。历史刊名、收录、当前订购及全文权限需另核实；结果为 Crossref 相关性检索。'}
