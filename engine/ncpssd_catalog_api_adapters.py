"""国家哲学社会科学文献中心公开题名/关键词题录分页。"""
import release_runtime
import time
import datetime
import re
import requests
URL = 'https://www.ncpssd.cn/searchHandler/search'
_last_request = 0.0

def ncpssd_catalog_search(keyword, page=1, page_size=10, include_abstract=False, field='all', start_year=None, end_year=None):
    global _last_request
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 80 or any((ord(c) < 32 or c == '"' for c in keyword)):
        raise ValueError('关键词须为1–80字且不含双引号或控制字符')
    if type(page) is not int or type(page_size) is not int or page < 1 or (not 1 <= page_size <= 10):
        raise ValueError('页码须大于零，每页1至10条')
    if not isinstance(include_abstract, bool):
        raise ValueError('摘要选项须为布尔值')
    fields = {'all': None, 'title': 'IKTE', 'keywords': 'IKST', 'abstract': 'IKRK', 'journal': 'CNEM', 'issn': 'ISSN', 'author': 'IKCR'}
    if field not in fields:
        raise ValueError('field 须为 all、title、keywords、abstract、journal、issn 或 author')
    q = keyword.strip()
    expr = f'(IKTE="{q}" OR IKPYTE="{q}"  OR IKST="{q}" OR IKET="{q}" OR IKSE="{q}")' if field == 'all' else f'{fields[field]}="{q}"'
    if field == 'author':
        if not re.fullmatch('[\\u3400-\\u9fffA-Za-z0-9 .·-]+', q) or re.search('\\b(?:AND|OR|NOT)\\b', q, re.I):
            raise ValueError('作者仅支持中英文、数字、空格及常见姓名分隔符')
        expr = f'((IKCR={q} OR IKCE={q}) AND ik_creator:"{q}"^20 OR (IKCRE="{q}"))'
    if (start_year is None) != (end_year is None):
        raise ValueError('开始和结束年份须同时提供')
    if start_year is not None:
        if type(start_year) is not int or type(end_year) is not int or (not 1000 <= start_year <= end_year <= 9999):
            raise ValueError('年份范围无效')
        expr = f'({expr}) AND years:[{start_year} TO {end_year}]'
    p = {'search': expr, 'pageNum': page, 'pageSize': page_size, 'sort': 'synUpdateType|DESC,date|DESC,ik_subject|DESC,id|DESC', 'sType': '0', 'ajaxKeys': q, 'customShowCondition': f'题名/关键词="{q}"'}
    delay = 1 - (time.monotonic() - _last_request)
    if delay > 0:
        time.sleep(delay)
    _last_request = time.monotonic()
    r = requests.post(URL, data=p, timeout=20)
    r.raise_for_status()
    out = r.json()
    if out.get('result') is not True or not isinstance(out.get('data'), dict):
        raise ValueError('文献中心未返回成功结果')
    d = out['data']
    total = d.get('total')
    hits = d.get('rows')
    if not isinstance(total, int) or not isinstance(hits, list):
        raise ValueError('未识别结果数量或题录')
    items = []
    for x in hits:
        if not x.get('title') or not x.get('id'):
            raise ValueError('题名或编号缺失')
        item = {'id': x['id'], 'title': x['title'], 'type': x.get('type'), 'creator': x.get('creator'), 'journal': x.get('cbw_name'), 'date': x.get('date'), 'issn': x.get('issn'), 'doi': x.get('doi'), 'keywords': x.get('subject')}
        raw_year = x.get('years')
        item['source_years_raw'] = raw_year if isinstance(raw_year, str) or type(raw_year) is int else None
        if start_year is not None:
            clean_year = str(raw_year) if isinstance(raw_year, str) or type(raw_year) is int else ''
            item['source_years_in_requested_range'] = start_year <= int(clean_year) <= end_year if re.fullmatch('[0-9]{4}', clean_year) else None
            raw_date = x.get('date')
            inside = None
            match = re.match('^(\\d{4})-(\\d{2})-(\\d{2})(?:T| |$)', raw_date) if isinstance(raw_date, str) else None
            if match:
                try:
                    source_date = datetime.date(*(int(v) for v in match.groups()))
                    inside = start_year <= source_date.year <= end_year
                except ValueError:
                    pass
            item['source_date_year_in_requested_range'] = inside
        if include_abstract:
            item['abstract'] = x.get('remark')
        items.append(item)
    result = {'source': '国家哲学社会科学文献中心题录', 'source_url': 'https://www.ncpssd.cn/', 'keyword': q, 'total': total, 'page': page, 'source_current_page': d.get('currentPage'), 'items': items, 'note': '题名/关键词公开题录搜索；站方 currentPage 实测为 0，不作为请求页码的确认。摘要如有可能截断；不取正文，机构身份和全文权限未验证。'}
    if field != 'all':
        result['field_requested'] = field
        result['note'] = '站方高级字段查询公开题录；词语可能分词，站方未回显字段，currentPage 实测为 0，不能确认请求页码。摘要字段检索不代表返回全文；机构及全文权限未核。'
    if start_year is not None:
        result['year_range_requested'] = {'start': start_year, 'end': end_year}
        result['note'] += ' 年份条件由站方执行且未回显；返回日期可能与所选年份不同，已标注原始日期年份是否在范围内，缺失或无法解析为未知。保留站方 years 原值并单独标记其是否在范围内；years 与 date 的具体含义和关系未确认，须核对原文；不据此删除记录。'
    return result
