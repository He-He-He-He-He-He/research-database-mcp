"""Campus IP authorized Minguo full-document database title results, first page."""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
URL = 'https://cadal.hytung.com.cn/main.aspx'

def search(keyword, limit=5, session=None, include_metadata=False, page=1, field='title', resource='book', start_year=None, end_year=None):
    if not isinstance(keyword, str) or not 1 <= len(keyword.strip()) <= 40:
        raise ValueError('关键词须为 1–40 字')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 5):
        raise ValueError('首屏最多 5 条')
    if not isinstance(include_metadata, bool):
        raise ValueError('include_metadata 须为布尔值')
    if type(page) is not int or not 1 <= page <= 100:
        raise ValueError('page 须为 1–100')
    if (start_year is None) != (end_year is None):
        raise ValueError('开始和结束年份须同时提供')
    if start_year is not None:
        if resource != 'book' or field != 'title':
            raise ValueError('年代组合目前仅验证图书标题')
        if type(start_year) is not int or type(end_year) is not int or (not 1911 <= start_year <= end_year <= 1949):
            raise ValueError('年代须为1911–1949的有序整数')
    resources = {'book': ('A0000', '圖書'), 'journal': ('B0000', '期刊'), 'newspaper': ('C0000', '報紙')}
    if resource not in resources:
        raise ValueError('不支持的资料类型')
    if resource != 'book' and field not in ('title', 'source', 'fulltext'):
        raise ValueError('期刊和报纸作者检索尚未验证')
    resource_code, resource_label = resources[resource]
    fields = {'title': 'Title', 'author': 'Author', 'source': 'Path', 'fulltext': 'FullText'}
    if field not in fields:
        raise ValueError('不支持的检索字段')
    q = keyword.strip()
    s = session or requests.Session()
    r = s.get(URL, timeout=20)
    r.raise_for_status()
    p = BeautifulSoup(r.content, 'html.parser')
    if not re.search('歡迎[：:]\\s*浙江大学', p.get_text(' ', strip=True)):
        raise RuntimeError('未确认浙江大学机构身份')
    data = {x['name']: x.get('value', '') for x in p.select('input[type=hidden][name]')}
    if not {'__VIEWSTATE', '__EVENTVALIDATION'}.issubset(data):
        raise RuntimeError('检索表单缺少状态字段')
    data.update({'cateCode': resource_code + ',', 'ddlField': fields[field], 'txtKeyword': q, 'rbtnlst': 'E', 'BtnExact': '搜  索'})
    if start_year is not None:
        data.update({'date': str(start_year) + '年', 'date1': str(end_year) + '年'})
    r = s.post(URL, data=data, timeout=25)
    r.raise_for_status()
    p = BeautifulSoup(r.content, 'html.parser')
    text = p.get_text(' ', strip=True)
    if not re.search('歡迎[：:]\\s*浙江大学', text):
        raise RuntimeError('结果页未确认浙江大学机构身份')

    def check_years(p):
        if start_year is not None:
            a = p.select_one('#date')
            b = p.select_one('#date1')
            if not a or not b or a.get('value') != str(start_year) + '年' or (b.get('value') != str(end_year) + '年'):
                raise RuntimeError('站方未回显年代范围')
    check_years(p)
    if field != 'title':
        selected = p.select_one('select[name=ddlField] option[selected]')
        if not selected or selected.get('value') != fields[field]:
            raise RuntimeError('源站未回显请求字段')
    if '沒有檢索到相關記錄' in text:
        result = {'source': '民国文献大全', 'institution': '浙江大学', 'query': q, 'page': page, 'total_records': 0, 'items': [], 'note': '站方精确模式；记录可能为同一书的不同页面，不等于独立图书；全文或影像未验证。'}
        if field != 'title':
            result['field_requested'] = field
        if resource != 'book':
            result['resource_requested'] = resource
            result['note'] = '站方精确模式的' + resource_label + '命中记录；记录数不等于刊物或报纸数量，全文及影像权限未验证。'
        if start_year is not None:
            result['year_filter_requested'] = {'start': start_year, 'end': end_year}
            result['note'] += ' 站方年代范围已回显，年代口径未确认，不能直接等同出版年。'
        if field == 'fulltext':
            result['note'] += ' 全文仅用于命中检索；可选元数据可能含短片段，不是完整正文。'
        return result
    count = re.search(re.escape(resource_label) + '[：:]\\s*([\\d,]+)\\s*條記錄', text)
    cells = p.select('#DataList .srcell')
    if not count or not cells or len(cells) > 5:
        raise RuntimeError('未识别图书结果或数量')
    total = int(count.group(1).replace(',', ''))
    offset = (page - 1) * limit
    source_page = 1
    all_cells = list(cells)
    if len(cells) != min(5, total):
        raise RuntimeError('原站首页记录数量不完整')
    needed = 0 if offset >= total else min(total, offset + limit)
    while len(all_cells) < needed:
        link = next((a for a in p.select('a[href]') if a.get_text(' ', strip=True) == '下一頁'), None)
        target = re.fullmatch("javascript:__doPostBack\\('([\\w$]+)','([^']*)'\\)", link.get('href', '')) if link else None
        if not target or target.group(1) != 'LinkBtnNext' or target.group(2) != '':
            raise RuntimeError('原站未提供可核验的下一页')
        data = {x['name']: x.get('value', '') for x in p.select('input[type=hidden][name]')}
        if not {'__VIEWSTATE', '__EVENTVALIDATION'}.issubset(data):
            raise RuntimeError('分页表单缺少状态字段')
        data.update({'__EVENTTARGET': 'LinkBtnNext', '__EVENTARGUMENT': '', 'cateCode': resource_code + ',', 'ddlField': fields[field], 'txtKeyword': q, 'rbtnlst': 'E'})
        if start_year is not None:
            data.update({'date': str(start_year) + '年', 'date1': str(end_year) + '年'})
        r = s.post(URL, data=data, timeout=25)
        r.raise_for_status()
        p = BeautifulSoup(r.content, 'html.parser')
        text = p.get_text(' ', strip=True)
        source_page += 1
        check_years(p)
        marker = re.search('第\\s*(\\d+)\\s*/\\s*(\\d+)\\s*頁', text)
        current = re.search(re.escape(resource_label) + '[：:]\\s*([\\d,]+)\\s*條記錄', text)
        next_cells = p.select('#DataList .srcell')
        if not re.search('歡迎[：:]\\s*浙江大学', text) or not marker or int(marker.group(1)) != source_page or (not current) or (int(current.group(1).replace(',', '')) != total) or (len(next_cells) != min(5, max(0, total - (source_page - 1) * 5))):
            raise RuntimeError('原站分页身份、页码或总数异常')
        if field != 'title':
            selected = p.select_one('select[name=ddlField] option[selected]')
            if not selected or selected.get('value') != fields[field]:
                raise RuntimeError('分页未回显请求字段')
        all_cells.extend(next_cells)
    items = []
    for x in all_cells[offset:offset + limit]:
        source = x.select_one('.derivation')
        title = x.select_one('.ctitle')
        if not source or (not title and (not (resource != 'book' and field == 'source'))):
            raise RuntimeError('结果缺少题名或来源')
        source_text = source.get_text('', strip=True)
        if resource != 'book' and (not source_text.startswith(resource_label + '·')):
            raise RuntimeError('结果资源类型与所选不符')
        item = {'source': source_text, 'title': title.get_text('', strip=True) if title else None}
        if include_metadata:
            summary = x.select_one('.summary')
            item['metadata_lines'] = list(summary.stripped_strings) if summary else None
        items.append(item)
    result = {'source': '民国文献大全', 'institution': '浙江大学', 'query': q, 'page': page, 'page_size': limit, 'total_records': total, 'items': items, 'note': '按请求页长连续返回，原站每页最多 5 条；图书标题精确模式，记录可能为同一书的不同页面，不等于独立图书；原始书目行可能缺失，全文或影像未验证。' if include_metadata else '按请求页长连续返回，原站每页最多 5 条；图书标题精确模式，记录可能为同一书的不同页面，不等于独立图书；全文或影像未验证。'}
    if field != 'title':
        result['field_requested'] = field
        result['note'] = '按请求页长连续返回，原站每页最多5条；站方精确模式及字段回显已核，匹配方式须核对；记录数非独立图书数，全文和影像权限未验证。'
    if resource != 'book':
        result['resource_requested'] = resource
        result['note'] = '按站方字段精确模式检索的' + resource_label + '命中记录，记录可能为不同文章或页面，不等于刊物或报纸数量；每页长度按请求值连续，全文与影像权限未验证。'
    if start_year is not None:
        result['year_filter_requested'] = {'start': start_year, 'end': end_year}
        result['note'] += ' 站方年代范围已回显，原始年代可能包含多个值，不能直接等同出版年。'
    if resource != 'book' and field == 'source':
        result['note'] += ' 出处命中可能没有文章标题，原样保留空值。'
    if field == 'fulltext':
        result['note'] += ' 全文仅用于命中检索；可选元数据可能含短片段，不是完整正文。'
    return result
