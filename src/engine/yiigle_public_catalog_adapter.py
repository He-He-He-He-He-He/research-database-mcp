"""Chinese Medical Association journal public metadata search, no abstract."""
import release_runtime
import requests
import re
import datetime
from urllib.parse import urlsplit
URL = 'https://www.yiigle.com/apiVue/search/searchList'

def search(keyword, page=1, limit=5, session=None, include_abstract=False, field='all', start_date=None, end_date=None):
    if not isinstance(keyword, str) or not 1 <= len(keyword.strip()) <= 100:
        raise ValueError('关键词须为 1–100 字')
    if not isinstance(page, int) or isinstance(page, bool) or page < 1:
        raise ValueError('页码须为正整数')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 10):
        raise ValueError('每页最多 10 条')
    if type(include_abstract) is not bool:
        raise ValueError('摘要开关须为布尔值')
    fields = {'all': None, 'title': '标题', 'author': '所有作者', 'first-author': '第一作者', 'journal': '刊名', 'keywords': '关键词', 'abstract': '摘要', 'doi': 'DOI'}
    if field not in fields:
        raise ValueError('不支持的检索字段')
    q = keyword.strip()
    if field == 'doi':
        if not re.fullmatch('10\\.[0-9]{4,9}/[A-Za-z0-9._-]+', q):
            raise ValueError('仅支持数字字母及点、下划线、连字符的 DOI')
    elif field != 'all' and (not re.fullmatch('[\\u3400-\\u9fffA-Za-z0-9 .·-]+', q) or re.search('\\b(?:AND|OR|NOT)\\b', q, re.I)):
        raise ValueError('高级检索关键词须使用普通文字')
    s = session or requests.Session()
    body = {'type': '', 'sortField': '', 'page': page, 'searchType': 'pt', 'pageSize': limit, 'queryString': q, 'query': '', 'searchText': q, 'searchLog': q, 'isAggregations': 'N', 'logintoken': None}
    if field != 'all':
        value = '"' + q + '"' if field == 'doi' else q if field in ('title', 'abstract') else q + '*'
        body.update({'searchType': 'gj', 'queryString': fields[field] + '=(' + value + ')'})
    if (start_date is None) != (end_date is None):
        raise ValueError('开始及结束日期须同时提供')
    if start_date is not None:
        if field not in ('title', 'author'):
            raise ValueError('日期范围目前仅验证 title 或 author')
        try:
            if not all((isinstance(v, str) and re.fullmatch('[0-9]{4}-[0-9]{2}-[0-9]{2}', v) for v in (start_date, end_date))) or datetime.date.fromisoformat(start_date) > datetime.date.fromisoformat(end_date):
                raise ValueError()
        except ValueError:
            raise ValueError('日期须为有效 YYYY-MM-DD 且开始不晚于结束') from None
        body['queryString'] += ' AND 出版日期= [' + start_date + ' TO ' + end_date + ']'
    r = s.post(URL, json=body, timeout=20)
    r.raise_for_status()
    j = r.json()
    d = j.get('data') if isinstance(j, dict) else None
    res = d.get('result') if isinstance(d, dict) else None
    if not isinstance(j, dict) or j.get('code') != 200 or (not isinstance(res, dict)) or (type(res.get('searchTotal')) is not int) or (res['searchTotal'] < 0) or (not isinstance(res.get('infos'), list)) or (len(res['infos']) > limit):
        raise RuntimeError('文献检索响应异常')
    expected = min(limit, max(0, res['searchTotal'] - (page - 1) * limit))
    if len(res['infos']) != expected:
        raise RuntimeError('站方返回条数与总数及页码不一致，可能数据变化或响应不完整')
    items = []
    for x in res['infos']:
        if not isinstance(x, dict) or type(x.get('artId')) is not int or (not isinstance(x.get('artTitle'), str)):
            raise RuntimeError('文献编号或题名缺失')
        if field == 'doi' and (not isinstance(x.get('artDoi'), str) or x['artDoi'].casefold() != q.casefold()):
            raise RuntimeError('源站返回的 DOI 与请求不符')
        item = {'id': x['artId'], 'title': x['artTitle'], 'authors': x.get('authorNames'), 'journal': x.get('journalCn'), 'year': x.get('artPubYear'), 'publication_date_raw': x.get('artPubDate'), 'volume': x.get('vol'), 'issue': x.get('issue'), 'doi': x.get('artDoi'), 'type': x.get('docType'), 'url': x.get('artUrl')}
        raw_url = x.get('artUrl')
        if raw_url is not None:
            try:
                u = urlsplit(raw_url) if isinstance(raw_url, str) else None
                valid = bool(u and u.scheme == 'https' and (u.hostname == 'rs.yiigle.com') and (not u.username) and (not u.password) and (u.port in (None, 443)) and (u.path == '/cmaid/' + str(x['artId'])) and (not u.query) and (not u.fragment))
            except ValueError:
                valid = False
            if not valid:
                item['url'] = None
                item['source_url_omitted'] = True
        if include_abstract:
            omitted = []
            for raw_key, out_key in (('artAbstract', 'abstract_raw'), ('keywords', 'keywords_raw'), ('subjectNames', 'subject_names_raw')):
                v = x.get(raw_key)
                valid = v is None or isinstance(v, str) or (isinstance(v, list) and all((isinstance(z, str) for z in v)))
                vals = [v] if isinstance(v, str) else v if isinstance(v, list) and valid else []
                if not valid or any((re.search('[a-z][a-z0-9+.-]*://|www\\.|(?:href|src)\\s*=|(?:token|session|sid|apikey|api_key)\\s*=', z, re.I) for z in vals)):
                    item[out_key] = None
                    omitted.append(raw_key)
                else:
                    item[out_key] = v
            if omitted:
                item['source_fields_omitted'] = omitted
        items.append(item)
    result = {'source': '中华医学期刊全文数据库', 'query': q, 'page': page, 'page_size': limit, 'total': res['searchTotal'], 'items': items[:limit], 'note': '原站公开检索的摘要及关键词原值，可能缺失或截断；未确认浙江大学机构身份及全文权限，不输出正文。' if include_abstract else '原站普通文献题录；本次未确认浙江大学机构身份或全文权限，不输出摘要和正文。'}
    result['note'] += ' 原站链接须匹配官方主机、记录编号且无参数；不符时省略并标记。'
    if include_abstract:
        result['note'] += ' 可选原字段若含链接、疑似凭据标记或异常结构则省略并标记。'
    if field != 'all':
        result['field_requested'] = field
        result['note'] += ' 站方高级字段检索未回显条件或页码，匹配可能包含其他语言或分词，相关性须核对。'
    if start_date is not None:
        result['date_range_requested'] = {'start': start_date, 'end': end_date}
        result['note'] += ' 站方未回显日期条件，样本仅验标题/作者；返回日期为源站 UTC 原值，边界时区须核对。'
    return result
