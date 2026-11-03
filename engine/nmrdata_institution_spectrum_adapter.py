"""微谱数据机构会话的单条 13C NMR 原表，不转换单位或结构。"""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
from nmrdata_institution_catalog_adapter import BASE, TURN, _identity
ID = re.compile('[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', re.I)

def spectrum(record_id, compound_name):
    if not isinstance(record_id, str) or not ID.fullmatch(record_id):
        raise ValueError('记录编号须为 UUID')
    if not isinstance(compound_name, str) or not compound_name.strip() or len(compound_name) > 200:
        raise ValueError('须提供化合物名称')
    with requests.Session() as s:
        r = s.get(TURN, timeout=20)
        r.raise_for_status()
        r = s.get(BASE + 'ChemicalSearch.aspx', timeout=20)
        r.raise_for_status()
        if not _identity(BeautifulSoup(r.content, 'html.parser')):
            raise RuntimeError('未确认浙江大学机构身份')
        r = s.get(BASE + 'data123help.aspx', params={'ccdid': "'" + record_id + "'"}, timeout=20)
        r.raise_for_status()
    p = BeautifulSoup(r.content, 'html.parser')
    label = p.select_one('#Label4')
    table = p.select_one('#grdData')
    if not label or not table or label.get_text(' ', strip=True) != compound_name.strip() + '的碳谱：' or (record_id.lower() not in r.text.lower()):
        raise RuntimeError('谱表编号或化合物名称不一致')
    headers = [x.get_text(' ', strip=True) for x in table.select('tr')[0].find_all('th', recursive=False)]
    if headers != ['Solvent', 'Position', '13C NMR']:
        raise RuntimeError('谱表列头异常')
    rows = []
    for tr in table.select('tr')[1:]:
        cells = []
        for td in tr.find_all('td', recursive=False):
            span = td.get('rowspan', '1')
            if not span.isdigit() or int(span) < 1:
                raise RuntimeError('谱表合并行异常')
            cells.append({'value': td.get_text(' ', strip=True), 'rowspan': int(span)})
        if len(cells) not in (2, 3):
            raise RuntimeError('谱表行结构异常')
        rows.append(cells)
    if not rows:
        raise RuntimeError('站方未返回谱表数据')
    return {'source': '微谱数据', 'institution': '浙江大学', 'record_id': record_id, 'compound': compound_name.strip(), 'headers': headers, 'rows': rows, 'note': '原站 13C NMR 表，原始字符串与合并行保留；站方页面未标示数值单位，此处不推定单位。单条表不代表化合物身份已独立鉴定；结构图未读取。'}
