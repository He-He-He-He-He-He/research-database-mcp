"""PWSannong agricultural encyclopedia public metadata search."""
import release_runtime
import re
import requests
URL = 'https://www.pwsannong.com/booklib/essearch/list'

def search(keyword, page=1, limit=5, session=None, include_summary=False):
    if not isinstance(keyword, str) or not 1 <= len(keyword.strip()) <= 100:
        raise ValueError('关键词须为 1–100 字')
    if not isinstance(page, int) or isinstance(page, bool) or page < 1:
        raise ValueError('页码须为正整数')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 10):
        raise ValueError('每页最多 10 条')
    if type(include_summary) is not bool:
        raise ValueError('include_summary 须为布尔值')
    q = keyword.strip()
    s = session or requests.Session()
    p = {'ps': limit, 'pi': page - 1, 'field': '', 'lang': 'chinese', 'classifyCode': '', 'classifyID': '', 'q': q, 'SiteID': '123', 'searchType': 'Wiki', 'sortData': '', 'sortType': '', 'title': '', 'author': '', 'series': '', 'keywords': '', 'sublibID': ''}
    r = s.get(URL, params=p, timeout=20)
    r.raise_for_status()
    j = r.json()
    total = j.get('total') if isinstance(j, dict) else None
    if type(total) not in (int, float) or total < 0 or int(total) != total or (not isinstance(j.get('hits'), list)) or (len(j['hits']) > limit):
        raise RuntimeError('百科检索响应异常')
    items = []
    for x in j['hits']:
        z = x.get('source') if isinstance(x, dict) else None
        if not isinstance(z, dict) or x.get('type') != 'Wiki' or (not isinstance(x.get('id'), str)) or (not isinstance(z.get('title'), str)):
            raise RuntimeError('百科题录或类别异常')
        item = {'id': x['id'], 'title': z['title'], 'author': z.get('authorName'), 'publish_date': z.get('publishDate')}
        if include_summary:
            summary = z.get('summary')
            if summary is not None and (not isinstance(summary, str) or re.search('[a-z][a-z0-9+.-]*://|www\\.|(?:href|src)\\s*=|(?:token|session|sid|apikey|api_key)\\s*=', summary, re.I)):
                item['summary_raw'] = None
                item['summary_omitted'] = True
            else:
                item['summary_raw'] = summary
        items.append(item)
    return {'source': '智汇三农农业百科', 'query': q, 'page': page, 'page_size': limit, 'total': total, 'items': items[:limit], 'note': '百科分类公开题录，原站总数保留原值；可选摘要为上游检索结果字段，可能不完整；含链接、凭据标志或异常结构时省略并标记。本次未确认学校机构身份或正文权限。'}
