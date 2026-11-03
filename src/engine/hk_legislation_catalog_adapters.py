"""香港律政司 DATA.GOV.HK 现行法例目录公开 JSON。"""
import release_runtime
import requests
BASE = 'https://resource.data.one.gov.hk/doj/data/hkel_list_c_all_{}.json'
FIELDS = {'zh-Hans': 'ChapterTitleSimplifiedChinese', 'zh-Hant': 'ChapterTitleTraditionalChinese', 'en': 'ChapterTitleEnglish'}

def hk_legislation_catalog(query, language='zh-Hant', page=1, page_size=20, timeout=30):
    if not isinstance(query, str) or not query.strip() or len(query) > 200:
        raise ValueError('关键词须为 1–200 字')
    if language not in FIELDS:
        raise ValueError('语言须为 zh-Hant、zh-Hans 或 en')
    if any((not isinstance(x, int) or isinstance(x, bool) for x in (page, page_size))) or page < 1 or (not 1 <= page_size <= 50):
        raise ValueError('页码须大于零，每页 1–50 条')
    url = BASE.format(language)
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    d = r.json()
    chapters = d.get('Chapter')
    if not isinstance(chapters, list) or d.get('lang') != language or d.get('pointOfTime') != 'c':
        raise ValueError('法例目录结构异常')
    q = query.strip().casefold()
    items = []
    for x in chapters:
        title = x.get(FIELDS[language], '')
        cap = x.get('CapNo', '')
        display = x.get('CapNoDisplay', '')
        if q not in title.casefold() and q not in str(cap).casefold() and (q not in str(display).casefold()):
            continue
        versions = []
        for v in x.get('Version', []):
            versions.append({'version_date': v.get('VersionDate'), 'url': v.get('Web')})
        items.append({'title': title, 'cap_no': cap, 'cap_no_display': display, 'legislation_type': x.get('LegislationType'), 'principal_ordinance': x.get('PrincipalOrdinance'), 'sub_legislation': x.get('SubLegislation'), 'versions': versions})
    start = (page - 1) * page_size
    return {'source': '香港特别行政区律政司，DATA.GOV.HK 现行法例目录', 'source_url': url, 'updated_at': d.get('UpdatedDateTime'), 'language': language, 'query': query.strip(), 'matched': len(items), 'page': page, 'page_size': page_size, 'returned': len(items[start:start + page_size]), 'next_page': page + 1 if start + page_size < len(items) else None, 'truncated': start + page_size < len(items), 'items': items[start:start + page_size], 'note': '本地按标题和章号包含匹配；目录包括主条例及附属法例，版本状态须逐条查看。每次重新读取目录，更新可能改变跨页顺序；数据按发布时点更新，不含法例正文；法律判断应核对香港电子法例当前正式文本及生效情况。'}
