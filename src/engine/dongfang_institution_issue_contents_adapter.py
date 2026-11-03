"""书同文《东方杂志》指定期次的栏目目录。"""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
from dongfang_institution_issue_adapter import BASE

def contents(issue_id, expected_issue):
    if not isinstance(issue_id, str) or not re.fullmatch('c[0-9]{1,10}', issue_id):
        raise ValueError('期次编号无效')
    if not isinstance(expected_issue, str) or not expected_issue.strip() or len(expected_issue) > 200:
        raise ValueError('须提供完整期次名称')
    with requests.Session() as s:
        r = s.get(BASE + 'Products/Search/QSL', timeout=20)
        r.raise_for_status()
        if not re.search('\\bzjdx\\b', BeautifulSoup(r.content, 'html.parser').get_text(' ', strip=True), re.I):
            raise RuntimeError('未识别学校账户标识')
        r = s.get(BASE + 'minguofy/api/catalog/get/MinGuoFY', params={'id': 'root'}, timeout=20)
        r.raise_for_status()
        root = r.json()
        if not isinstance(root, list):
            raise RuntimeError('原站期次总目异常')
        matching = [x for x in root if isinstance(x, dict) and x.get('id') == issue_id and (x.get('text') == expected_issue.strip())]
        if len(matching) != 1:
            raise RuntimeError('期次编号和名称不匹配')
        r = s.get(BASE + 'minguofy/api/catalog/get/MinGuoFY', params={'id': issue_id}, timeout=20)
        r.raise_for_status()
        data = r.json()
    if not isinstance(data, list):
        raise RuntimeError('期次栏目响应异常')
    sections = []
    for x in data:
        attr = x.get('li_attr') if isinstance(x, dict) else None
        if not isinstance(x, dict) or not isinstance(x.get('text'), str) or (not isinstance(attr, dict)) or (not str(attr.get('rel', '')).isdigit()):
            raise RuntimeError('栏目数据异常')
        sections.append({'title': x['text'], 'page_id': str(attr['rel']), 'type': x.get('type'), 'has_children': x.get('children')})
    return {'source': '书同文东方杂志总目', 'account_marker': 'zjdx', 'issue_id': issue_id, 'issue': expected_issue.strip(), 'sections': sections, 'note': '站方期次下栏目目录；栏目不等于文章或全文，栏目编号是原站页面标识，未验证正文或逐项权限。'}
