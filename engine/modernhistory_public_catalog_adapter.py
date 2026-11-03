"""抗日战争与近代中日关系文献数据平台的公开检索题录。"""
import release_runtime
import html
import re
import requests
URL = 'https://www.modernhistory.org.cn/backend-prod/esBook/findByPage'

def search(keyword, page=1, limit=5):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100 or re.search('[\\x00-\\x1f]', keyword):
        raise ValueError('关键词须为 1–100 字单行文本')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 1000):
        raise ValueError('页码须为 1–1000')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 20):
        raise ValueError('每页数量须为 1–20')
    q = keyword.strip()
    payload = {'secondKeyword': '', 'currentPage': page, 'docType': 'total', 'keyword': q, 'pageSize': limit, 'firstFieldName': '', 'firstFieldValue': '', 'secondFieldName': '', 'secondFieldValue': '', 'startDate': '', 'endDate': '', 'orderByDownload': '', 'orderByGmtCreate': '', 'orderByPublishTime': ''}
    r = requests.post(URL, json=payload, timeout=30)
    r.raise_for_status()
    try:
        j = r.json()
    except ValueError:
        raise RuntimeError('原站未返回 JSON') from None
    if not isinstance(j, dict) or str(j.get('code')) != '200':
        raise RuntimeError('原站返回业务错误')
    d = j.get('result')
    if not isinstance(d, dict) or not isinstance(d.get('dataList'), list) or len(d['dataList']) > limit:
        raise RuntimeError('原站检索结构异常')
    total, pages = (d.get('totalSize'), d.get('totalPage'))
    if not str(total).isdigit() or not str(pages).isdigit():
        raise RuntimeError('原站检索总数异常')
    expected = min(limit, max(0, int(total) - (page - 1) * limit))
    if len(d['dataList']) != expected:
        raise RuntimeError('站方返回条数与总数及页码不一致，可能数据变化或响应不完整')
    items = []
    for x in d['dataList']:
        if not isinstance(x, dict) or x.get('id') is None or (not isinstance(x.get('title'), str)):
            raise RuntimeError('原站记录缺少编号或标题')
        title = html.unescape(re.sub('<[^>]*>', '', x['title']))
        item = {'id': str(x['id']), 'title': title, 'title_raw': x['title'], 'doc_type_raw': x.get('docType'), 'author_raw': x.get('firstResponsible'), 'publish_time_raw': x.get('publishTime'), 'publisher_raw': x.get('publisher'), 'organization_raw': x.get('orgName'), 'language_raw': x.get('language'), 'page_amount_raw': x.get('pageAmount'), 'original_title_raw': x.get('originalTitle'), 'keywords_raw': x.get('keyWords'), 'publication_time_full_raw': x.get('publishTimeAll'), 'series_name_raw': x.get('seriesName'), 'volume_information_raw': x.get('volumeInfoAllStr'), 'edition_raw': x.get('version'), 'content_description_raw': x.get('contentDesc')}
        omitted = []
        for key, value in list(item.items()):
            if key == 'id':
                continue
            valid = value is None or isinstance(value, (str, int, float, bool)) or (isinstance(value, list) and all((isinstance(z, str) for z in value)))
            vals = [value] if isinstance(value, str) else value if isinstance(value, list) and valid else []
            if not valid or any((re.search('[a-z][a-z0-9+.-]*://|www\\.|(?:href|src)\\s*=|(?:token|session|sid|apikey|api_key)\\s*=', html.unescape(z), re.I) for z in vals)):
                item[key] = None
                omitted.append(key)
        if omitted:
            item['source_fields_omitted'] = omitted
        items.append(item)
    return {'source': '抗日战争与近代中日关系文献数据平台公开题录', 'query': q, 'page_requested': page, 'page_size': limit, 'total_raw': total, 'total_pages_raw': pages, 'items': items, 'note': '公开检索题录；原站未回显请求页码，文献类型、主题词、内容说明及出版字段按原样保留，缺失不作推断。安全原始题名保留高亮，敏感或异常字段省略并标记；按总数校验页长，数据可能变化。机构身份、逐条原文和下载权限未验证；浙大馆方说明下载需注册。'}
