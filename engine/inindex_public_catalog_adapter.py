"""Public Inindex literature, office and toponym catalog searches."""
import release_runtime
import requests
BASE = 'https://api.cloud.xyinde.com/'

def search(kind, keyword, page=1, limit=10, session=None, start_year=None, end_year=None, field='keyword'):
    if kind not in ('literature', 'office', 'toponym'):
        raise ValueError('类型须为 literature、office 或 toponym')
    fields = {'keyword': '关键字', 'title': '书名', 'author': '作者', 'dynasty': '朝代'}
    if field not in fields:
        raise ValueError('不支持的检索字段')
    if field != 'keyword' and kind != 'literature':
        raise ValueError('指定字段仅支持文献目录')
    if not isinstance(keyword, str) or not 1 <= len(keyword.strip()) <= 100:
        raise ValueError('关键词须为 1–100 字')
    if not isinstance(page, int) or isinstance(page, bool) or page < 1:
        raise ValueError('页码须为正整数')
    size = 10 if kind == 'literature' else 20
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= size):
        raise ValueError('每页最多 ' + str(size) + ' 条')
    if (start_year is None) != (end_year is None):
        raise ValueError('开始和结束年份须同时提供')
    if start_year is not None:
        if kind != 'toponym':
            raise ValueError('年份筛选目前仅支持地名')
        if type(start_year) is not int or type(end_year) is not int or (not 1 <= start_year <= end_year <= 9999):
            raise ValueError('年份须为顺序正确的公元 1–9999 整数')
    q = keyword.strip()
    s = session or requests.Session()
    if kind == 'literature':
        body = {'page': page, 'pageSize': limit, 'leftNum': 0, 'rightNum': 0, 'keyWord': '', 'list': [{'joinType': '', 'searchType': fields[field], 'inputContent': q}]}
        r = s.post(BASE + 'literature/v2/book/advanceSearch', json=body, timeout=20)
    else:
        data = {'keyWordList': q, 'page': str(page), 'pageSize': str(limit), 'startYear': str(start_year) if start_year is not None else '', 'endYear': str(end_year) if end_year is not None else ''}
        if kind == 'toponym':
            data['yearType'] = 'NORMAL'
        path = 'toponymy/getToponymyList' if kind == 'toponym' else 'office/getOfficeList'
        r = s.post(BASE + 'wuzheng/v2/' + path, data=data, timeout=20)
    r.raise_for_status()
    j = r.json()
    if not isinstance(j, dict) or j.get('success') is not True:
        raise RuntimeError('站方搜索失败')
    d = j.get('data') if kind == 'literature' else j.get('npage')
    rows = d.get('records') if kind == 'literature' and isinstance(d, dict) else j.get('list')
    total = d.get('total') if kind == 'literature' and isinstance(d, dict) else d.get('totalCount') if isinstance(d, dict) else None
    if not isinstance(d, dict) or type(total) is not int or total < 0 or (not isinstance(rows, list)) or (len(rows) > limit) or (kind != 'literature' and (d.get('page') != page or d.get('pageSize') != limit)):
        raise RuntimeError('站方响应结构或页码异常')
    expected = min(limit, max(0, total - (page - 1) * limit))
    if len(rows) != expected:
        raise RuntimeError('站方返回条数与总数及页码不一致，可能数据变化或响应不完整')
    items = []
    for x in rows:
        if not isinstance(x, dict):
            raise RuntimeError('题录异常')
        if kind == 'literature':
            if not isinstance(x.get('id'), str) or not x['id'].isdigit() or (not isinstance(x.get('title'), str)):
                raise RuntimeError('文献字段缺失')
            author = x.get('author')
            dynasty = x.get('dynasty')
            category = x.get('category')
            items.append({'id': x['id'], 'title': x['title'], 'author': author.get('titleCn') if isinstance(author, dict) else None, 'author_role': x.get('authorTag'), 'dynasty': dynasty.get('title') if isinstance(dynasty, dict) else None, 'edition_source': x.get('source'), 'category': category.get('title') if isinstance(category, dict) else None})
        elif kind == 'office':
            if type(x.get('id')) is not int or not isinstance(x.get('name'), str):
                raise RuntimeError('职官字段缺失')
            items.append({'id': x['id'], 'name': x['name'], 'name_simplified': x.get('nameChs'), 'dynasty': x.get('dynasty'), 'organization': x.get('organization'), 'superior': x.get('supername'), 'grade': x.get('grade'), 'established': x.get('establishCustom'), 'abolished': x.get('abolishCustom')})
        else:
            if type(x.get('id')) is not int or not isinstance(x.get('toponymy'), str):
                raise RuntimeError('地名字段缺失')
            items.append({'id': x['id'], 'name': x['toponymy'], 'name_simplified': x.get('toponymyChs'), 'dynasty': x.get('dynasty'), 'superior': x.get('isTheUnit'), 'established': x.get('establishcommon'), 'abolished': x.get('abolishcommon')})
    result = {'source': '引得平台', 'kind': kind, 'query': q, 'page': page, 'page_size': limit, 'total': total, 'items': items[:limit], 'note': '公开目录检索；部分网页总数曾与接口不一致，此处为接口原值。是否属于浙江大学订购范围、资料详情和全文均未验证。'}
    result['note'] += ' 已按源总数与请求页次核对条数；职官、地名越界时站方可能回退末页，本接口拒绝页码不符；文献页码未回显，数据可能变化。'
    if field != 'keyword':
        result['field_requested'] = field
        result['note'] += ' 站方未回显检索条件，繁简匹配及逐项结果须核对。'
    if start_year is not None:
        result['year_filter_requested'] = {'start': start_year, 'end': end_year}
        result['note'] += ' 站方不回显年份条件；筛选规则未完全确认。地名样本显示可能要求整个存续区间落在所选范围内，不可视为在该范围任意年份存续的完整列表。'
    return result
