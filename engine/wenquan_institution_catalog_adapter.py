"""Wenquan ZJU institution catalog search; temporary session token is not stored."""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
BASE = 'https://lib-zju.wqxuetang.com/'

def _plain(v):
    return BeautifulSoup(v, 'html.parser').get_text('', strip=True) if isinstance(v, str) else v

def search(keyword, page=1, limit=5, session=None, include_description=False, author='', start_year=None, end_year=None, resource_type='all'):
    if not isinstance(keyword, str) or not 1 <= len(keyword.strip()) <= 100:
        raise ValueError('关键词须为 1–100 字')
    if not isinstance(page, int) or isinstance(page, bool) or page < 1:
        raise ValueError('页码须为正整数')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 10):
        raise ValueError('每页最多 10 条')
    if not isinstance(include_description, bool):
        raise ValueError('include_description 须为布尔值')
    types = {'all': None, 'book': '1', 'journal': '8'}
    if resource_type not in types:
        raise ValueError('资源类型须为 all、book 或 journal')
    if not isinstance(author, str) or len(author) > 100 or any((ord(c) < 32 for c in author)):
        raise ValueError('作者须为不超过100字的单行文本')
    if resource_type == 'journal' and (author.strip() or start_year is not None or end_year is not None):
        raise ValueError('期刊与作者/年份组合尚未验证')
    if (start_year is None) != (end_year is None):
        raise ValueError('开始和结束年份须同时提供')
    if start_year is not None and (type(start_year) is not int or type(end_year) is not int or (not 1000 <= start_year <= end_year <= 9999)):
        raise ValueError('年份范围无效')
    q = keyword.strip()
    s = session or requests.Session()
    s.get(BASE, timeout=20).raise_for_status()
    r = s.post(BASE + 'api/v7/rz/jxjwt', params={'s': 'wqxuetang'}, timeout=20)
    r.raise_for_status()
    j = r.json()
    token = j.get('data') if isinstance(j, dict) else None
    if not isinstance(token, str) or not token:
        raise RuntimeError('站方会话初始化失败')
    headers = {'Authorization': token}
    r = s.get(BASE + 'api/v7/search/libdata', headers=headers, timeout=20)
    r.raise_for_status()
    j = r.json()
    identity = j.get('data') if isinstance(j, dict) else None
    if not isinstance(j, dict) or j.get('errcode') != 0 or (not isinstance(identity, dict)) or (identity.get('name') != '浙江大学') or (identity.get('inip') is not True):
        raise RuntimeError('未确认浙大校内访问')
    params = {'kw': q, 'pn': page, 'size': limit, 'webType': 2}
    if types[resource_type] is not None:
        params['type'] = types[resource_type]
    if author.strip():
        params['author'] = author.strip()
    if start_year is not None:
        params.update({'begindate': str(start_year), 'enddate': str(end_year)})
    r = s.get(BASE + 'v2/search/index', params=params, headers=headers, timeout=20)
    r.raise_for_status()
    j = r.json()
    d = j.get('data') if isinstance(j, dict) else None
    info = d.get('pageinfo') if isinstance(d, dict) else None
    if not isinstance(j, dict) or j.get('errcode') != 0 or (not isinstance(d, dict)) or (not isinstance(info, dict)) or (info.get('pn') != page) or (type(info.get('totalrecord')) is not int) or (info['totalrecord'] < 0) or (not isinstance(d.get('list'), list)) or (len(d['list']) > limit):
        raise RuntimeError('检索响应异常')
    expected = min(limit, max(0, info['totalrecord'] - (page - 1) * limit))
    if len(d['list']) != expected:
        raise RuntimeError('站方返回条数与总数及页码不一致，可能数据变化或响应不完整')
    items = []
    for x in d['list']:
        if not isinstance(x, dict) or not isinstance(x.get('id'), str) or (not isinstance(x.get('name'), str)):
            raise RuntimeError('题录编号或标题缺失')
        if resource_type != 'all' and str(x.get('type')) != types[resource_type]:
            raise RuntimeError('站方资源类型与请求不一致')
        item = {'id': x['id'], 'title': _plain(x['name']), 'type': x.get('type'), 'author': _plain(x.get('author')), 'publisher': _plain(x.get('pub')), 'publish_date': x.get('pubdate'), 'isbn': x.get('isbn'), 'year': x.get('year')}
        omitted = []
        for k, out, display in (('name', 'source_name_raw', 'title'), ('author', 'source_author_raw', 'author'), ('pub', 'source_pub_raw', 'publisher')):
            v = x.get(k)
            if v is not None and (not isinstance(v, str) or re.search('[a-z][a-z0-9+.-]*://|www\\.|(?:href|src)\\s*=|(?:token|session|sid|apikey|api_key)\\s*=', v, re.I)):
                item[out] = None
                omitted.append(k)
                cleaned = item[display]
                if cleaned is not None and (not isinstance(cleaned, str) or re.search('[a-z][a-z0-9+.-]*://|www\\.|(?:token|session|sid|apikey|api_key)\\s*=', cleaned, re.I)):
                    item[display] = None
            else:
                item[out] = v
        if include_description:
            for k, out in (('descript', 'description_raw'), ('edt_view', 'editorial_view_raw')):
                v = x.get(k)
                valid = v is None or isinstance(v, str) or (isinstance(v, list) and all((isinstance(z, str) for z in v)))
                vals = [v] if isinstance(v, str) else v if isinstance(v, list) and valid else []
                if not valid or any((re.search('[a-z][a-z0-9+.-]*://|www\\.|(?:href|src)\\s*=|(?:token|session|sid|apikey|api_key)\\s*=', z, re.I) for z in vals)):
                    item[out] = None
                    omitted.append(k)
                else:
                    item[out] = v
        if omitted:
            item['source_fields_omitted'] = omitted
        items.append(item)
    result = {'source': '文泉学堂浙大站', 'institution': '浙江大学', 'campus_ip': True, 'query': q, 'page': page, 'page_size': limit, 'total': info['totalrecord'], 'items': items[:limit], 'note': '站方机构识别后全部类型检索，资源类型保留原站值；不代表所有资源均有全文权限。'}
    if include_description:
        result['description_note'] = '安全简介与编辑推荐原值保留；含链接、疑似凭据或异常结构时相关字段省略并标记。'
    if author.strip() or start_year is not None:
        result['filters_requested'] = {'author': author.strip() or None, 'start_year': start_year, 'end_year': end_year}
        result['note'] += ' 站方未回显作者或年份筛选，已按样本抽验，匹配及逐项权限需核对。'
    if resource_type != 'all':
        result['resource_type_requested'] = resource_type
        result['note'] = '站方机构识别后按资源类型请求，逐项类型已核；关键词可能匹配标题之外的字段，未确认逐项全文权限。'
        if author.strip() or start_year is not None:
            result['note'] += ' 作者或年份筛选未由站方回显，匹配须逐项核对。'
    result['note'] += ' 已按源总数及回显页码校验条数，数据可能变化；source_name_raw/source_author_raw/source_pub_raw 保留安全原字段及高亮，敏感或异常值省略并标记。'
    return result
