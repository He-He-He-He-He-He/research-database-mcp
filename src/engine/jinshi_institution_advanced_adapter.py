"""历代进士浙大 IP 高级查询：姓名与朝代的且关系。"""
import release_runtime
import re, requests
from bs4 import BeautifulSoup
BASE = 'https://examination.ancientbooks.cn/docDengke/'

def search(name, dynasty, page=1, second_field='dynasty'):
    for value in (name, dynasty):
        if not isinstance(value, str) or not 1 <= len(value.strip()) <= 100 or (not re.fullmatch('[\\u3400-\\u9fffA-Za-z0-9 .·-]+', value.strip())) or re.search('\\b(?:AND|OR|NOT)\\b', value, re.I):
            raise ValueError('姓名和朝代须使用普通字符')
    if type(page) is not int or not 1 <= page <= 1000:
        raise ValueError('页码须为1–1000')
    fields = {'dynasty': 'dynasty', 'birth': 'sourceBirth', 'subject': 'subject'}
    if second_field not in fields:
        raise ValueError('second_field 须为 dynasty、birth 或 subject')
    name = name.strip()
    dynasty = dynasty.strip()
    params = {'bookType': '', 'searchType': '2', 'firstSearch': name, 'type': 'fullName', 'txt': dynasty, 'typeitem': fields[second_field], 'operation': 'AND,AND', 'isRelevance': 'true', 'isExact': 'true', 'pageNo': str(page), 'pageSize': '15'}
    with requests.Session() as s:
        r = s.get(BASE + 'dkExpertSearch.jspx', params=params, timeout=25)
        r.raise_for_status()
        if '当前机构: 浙江大学' not in BeautifulSoup(r.content, 'html.parser').get_text(' ', strip=True):
            raise RuntimeError('未确认浙江大学机构身份')
        r = s.get(BASE + 'dkExpertSearchTable.jspx', params=params, timeout=25)
        r.raise_for_status()
        try:
            j = r.json()
        except ValueError:
            raise RuntimeError('高级检索未返回 JSON') from None
    if not isinstance(j, dict) or j.get('code') != 0 or type(j.get('count')) is not int or (j['count'] < 0) or (not isinstance(j.get('data'), list)) or (len(j['data']) > 15):
        raise RuntimeError('高级检索响应异常')
    if any((not isinstance(x, dict) or not x.get('content_id') or (not isinstance(x.get('fullName'), str)) for x in j['data'])):
        raise RuntimeError('结果字段缺失')
    result = {'source': '历代进士登科数据库', 'institution': '浙江大学', 'name_query': name, 'dynasty_query': dynasty, 'page': page, 'total': j['count'], 'source_total_pages': j.get('totalPage'), 'items': j['data'], 'note': '按站方高级检索请求姓名且朝代，王/明两页与张/清首屏抽验；保留原始字段及高亮，站方未回显条件或页码，匹配规则须核对；零结果仍可能报告1页，详情字体编码及逐条权限未验证。'}
    if second_field != 'dynasty':
        result.pop('dynasty_query')
        result['second_field_requested'] = second_field
        result['second_query'] = dynasty
        result['note'] = '按站方高级检索请求姓名且指定字段；王/浙江前2页和王/进士首屏抽验。保留原始字段及高亮，站方未回显条件或页码，匹配规则须核对；零结果可能报告1页，详情字体编码及逐条权限未验证。'
    return result
