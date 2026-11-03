"""国别区域与全球治理平台公开资源检索单页题录。"""
import release_runtime
import html
import re
import requests
URL = 'https://www.crggcn.com/skwx_crgg/search/list'

def search(keyword, page=1, limit=5, include_abstract=False, field='all', resource_type='all'):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100 or any((c in keyword for c in '\r\n')):
        raise ValueError('关键词须为1–100字单行文本')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 10000):
        raise ValueError('页码须为1–10000')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 10):
        raise ValueError('每页数量须为1–10')
    if type(include_abstract) is not bool:
        raise ValueError('摘要开关须为布尔值')
    fields = {'all': 'All', 'title': 'searchTitle', 'author': 'authors', 'keywords': 'keyWords', 'summary': 'summary', 'subject': 'subjectWords'}
    if field not in fields:
        raise ValueError('field 须为 all、title、author、keywords、summary 或 subject')
    types = {'all': 'all', 'article': 'Literature', 'book': 'Book', 'figure': 'ImageTable', 'news': 'News', 'audio': 'AudioBook'}
    if resource_type not in types:
        raise ValueError('resource_type 须为 all、article、book、figure、news 或 audio')
    if field == 'subject' and resource_type not in ('article', 'book'):
        raise ValueError('主题词目前仅验证 article 或 book')
    p = {'q': keyword.strip(), 'pi': str(page - 1), 'ps': str(limit), 't': types[resource_type], 'field': fields[field], 'lang': 'chinese', 'classifyParam': '', 'siteID': '25'}
    r = requests.post(URL, data=p, timeout=30)
    r.raise_for_status()
    try:
        j = r.json()
    except ValueError:
        raise RuntimeError('国别平台未返回 JSON') from None
    if not isinstance(j, dict) or not isinstance(j.get('total'), int) or (not isinstance(j.get('hits'), list)) or (len(j['hits']) > limit):
        raise RuntimeError('国别平台检索响应异常')
    items = []
    for hit in j['hits']:
        if resource_type != 'all' and (not isinstance(hit, dict) or hit.get('type') != types[resource_type]):
            raise RuntimeError('站方记录类型与请求不一致')
        x = hit.get('source') if isinstance(hit, dict) else None
        if not isinstance(x, dict) or not isinstance(x.get('searchTitle'), str) or (not isinstance(hit.get('id'), str)):
            raise RuntimeError('题录编号或标题缺失')
        item = {'id': hit['id'], 'type': hit.get('type'), 'title': html.unescape(re.sub('<[^>]*>', '', x['searchTitle'])), 'authors': x.get('authors'), 'published': x.get('publishDate'), 'book': x.get('bookName') or x.get('bookTitle'), 'content_id': x.get('ID') if type(x.get('ID')) in (int, str) else None}
        if include_abstract:
            item.update({'abstract': x.get('summary'), 'keywords': x.get('keyWords'), 'isbn': x.get('ISBN')})
        items.append(item)
    result = {'source': '国别区域与全球治理数据平台公开题录', 'query': keyword.strip(), 'field': '全部字段', 'page': page, 'page_size': limit, 'total': j['total'], 'items': items, 'note': '未登录会话取得的中文资源题录和站方摘要字段，关键词可匹配标题之外字段；摘要可能为空或截断，未识别学校机构身份，不含正文或统计数值，权限未验证。' if include_abstract else '未登录会话取得的中文资源题录，关键词可匹配标题之外字段；本次未识别学校机构身份，不含正文或统计数值，权限未验证。'}
    if field != 'all':
        result['field_requested'] = field
        result['note'] += ' 按站方字段请求，可能分词；站方未回显字段或页码，摘要字段仅查询题录。'
    if resource_type != 'all':
        result['resource_type_requested'] = resource_type
        result['note'] += ' 站方类型计数不应直接相加；搜索可能分词或模糊匹配，图表仅题录，非统计值。'
    if field == 'subject':
        result['note'] += ' 站方不返回主题词，部分标题和关键词未包含查询词，相关性未逐条核验。'
    return result
