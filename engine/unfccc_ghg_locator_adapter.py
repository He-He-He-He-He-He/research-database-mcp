"""UNFCCC GHG Locator public site data service: reporting party to observations."""
import release_runtime
import json, re, requests
BASE = 'https://datahub-prd-app02.azurewebsites.net/api/GHG_Master/'
PAGE = 'https://data.unfccc.int/locator/'
SOURCE = 'https://unfccc.int/process-and-meetings/transparency-and-reporting/reporting-and-review/transparency-data-and-tools/greenhouse-gas-data/information-on-data-sources'

def _post(path, payload):
    if not re.fullmatch('(?:MasterPartyList_New|MasterSubmissionsList/\\d+|BindCategoryList_New_Latest|BindVariableList|GraphNew)', path):
        raise ValueError('无效服务路径')
    with requests.post(BASE + path, json=payload, headers={'Origin': 'https://data.unfccc.int'}, timeout=(10, 50), stream=True, allow_redirects=False) as r:
        if r.is_redirect:
            raise RuntimeError('官网服务发生跳转')
        r.raise_for_status()
        body = bytearray()
        for b in r.iter_content(65536):
            body.extend(b)
            if len(body) > 8000000:
                raise ValueError('响应过大，请缩小选择')
    obj = json.loads(body, parse_float=str)
    if not isinstance(obj, list) or any((not isinstance(x, dict) for x in obj)):
        raise RuntimeError('UNFCCC 官网服务响应异常')
    return obj

def _positive(x, name):
    if type(x) is not int or not 1 <= x <= 99999999:
        raise ValueError(name + ' 须为正整数')
    return x

def _page(rows, keyword, limit, offset):
    if not isinstance(keyword, str) or len(keyword) > 150 or type(limit) is not int or (not 1 <= limit <= 100) or (type(offset) is not int) or (not 0 <= offset <= 100000):
        raise ValueError('关键词或分页无效')
    term = keyword.casefold().strip()
    found = [x for x in rows if term in json.dumps(x, ensure_ascii=False).casefold()]
    return {'matched': len(found), 'offset': offset, 'items': found[offset:offset + limit]}

def parties(keyword='', limit=30, offset=0):
    rows = _post('MasterPartyList_New', None)
    return {'site': PAGE, 'source_url': BASE + 'MasterPartyList_New', **_page(rows, keyword, limit, offset), 'note': '官网当前国家、地区及分组树；childId 可能是地区组而非国家，须核对名称和父级。当前列表不是历史快照。'}

def submissions(party):
    _positive(party, '缔约方')
    rows = _post('MasterSubmissionsList/' + str(party), None)
    return {'site': PAGE, 'source_url': BASE + 'MasterSubmissionsList/' + str(party), 'party': party, 'items': rows, 'note': '官网当前提交版本列表；名称中的年份/版本不等于经过核实的提交或发布日期。空列表不是零排放。'}

def _context(party, submission):
    _positive(party, '缔约方')
    _positive(submission, '提交版本')
    if not any((x.get('value') == submission for x in submissions(party)['items'])):
        raise ValueError('所选提交版本不在该缔约方当前列表中')
    return {'SubmissionIds': [submission], 'AdditionalProp3': 'ANY', 'LatestSubmissionIds': [], 'partyids': [party], 'ExcludeChecked': False}

def categories(party, submission, keyword='', limit=30, offset=0):
    body = _context(party, submission)
    rows = _post('BindCategoryList_New_Latest', body)
    return {'site': PAGE, 'source_url': BASE + 'BindCategoryList_New_Latest', 'party': party, 'submission': submission, **_page(rows, keyword, limit, offset), 'note': '当前选定提交版本的平面分类树，保留 parent_id 与启用状态；分类父子层级可能重叠，勿直接加总。'}

def _variables(party, submission, category):
    _positive(category, '分类')
    ctx = _context(party, submission)
    cats = _post('BindCategoryList_New_Latest', ctx)
    if not any((x.get('id') == category for x in cats)):
        raise ValueError('分类不属于选定提交版本')
    payload = {'CategoryId': [category], 'ExcludeChecked': False, 'NotationKeyId': 'ANY', 'SubmissionIds': [submission], 'LatestSubmissionIds': [], 'PartyIds': [party]}
    return _post('BindVariableList', payload)

def variables(party, submission, category, keyword='', limit=30, offset=0):
    rows = _variables(party, submission, category)
    return {'site': PAGE, 'source_url': BASE + 'BindVariableList', 'party': party, 'submission': submission, 'category': category, **_page(rows, keyword, limit, offset), 'note': '变量名称含气体、分类、是否包含土地利用和单位等，须完整阅读；代码可选不保证所有年份有值。'}

def observations(party, submission, category, variable, start=None, end=None):
    _positive(variable, '变量')
    rows = _variables(party, submission, category)
    if not any((x.get('variableId') == variable for x in rows)):
        raise ValueError('变量不属于选定分类及提交版本')
    for y in (start, end):
        if y is not None and (type(y) is not int or not 1900 <= y <= 2100):
            raise ValueError('年份无效')
    if start is not None and end is not None and (start > end):
        raise ValueError('起始年晚于结束年')
    payload = {'AdditionalProp1': [variable], 'AdditionalProp2': [submission], 'AdditionalProp5': [], 'AdditionalProp3': [party], 'AdditionalProp4': 2000, 'IsLatestSubmission': False}
    obs = _post('GraphNew', payload)
    if any((x.get('partyId') != party or x.get('submissionId') != submission or x.get('variableId') != variable for x in obs)):
        raise RuntimeError('官网返回选择范围外的数据')

    def selected(row):
        y = str(row.get('inventoryYear', ''))
        if not re.fullmatch('\\d{4}', y):
            return start is None and end is None
        return (start is None or int(y) >= start) and (end is None or int(y) <= end)
    filtered = [x for x in obs if selected(x)]
    return {'site': PAGE, 'source_url': BASE + 'GraphNew', 'source_information': SOURCE, 'party': party, 'submission': submission, 'category': category, 'variable': variable, 'start': start, 'end': end, 'upstream_returned': len(obs), 'returned': len(filtered), 'records': filtered, 'note': 'UNFCCC 官网前端使用的公开服务（接口可能变更）；记录来自缔约方提交，不等同卫星实测或全球统一模型。按观测年本地过滤，保留提交版本、原报告字符串、符号及单位；numberValue 小数以字符串保精度。提交名中的年份不证明该版本在任何历史截止日已经公开，当前数据可能更新。LULUCF、间接排放、气体和单位均须按变量名区分。'}
