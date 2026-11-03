"""温州数据开放平台：按目录编号读取完全开放资源的官方预览。"""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
BASE = 'https://data.wenzhou.gov.cn/jdop_front/'

def _id(iid):
    if not re.fullmatch('[1-9][0-9]{0,8}', str(iid)) or isinstance(iid, bool):
        raise ValueError('目录编号无效')
    return str(iid)

def detail(iid):
    iid = _id(iid)
    r = requests.get(BASE + 'detail/data.do', params={'iid': iid}, timeout=30, allow_redirects=False)
    r.raise_for_status()
    if r.is_redirect or 'text/html' not in r.headers.get('Content-Type', '').lower():
        raise RuntimeError('详情未返回预期网页')
    s = BeautifulSoup(r.content, 'html.parser')
    metadata = {}
    for tr in s.find_all('tr'):
        cells = tr.find_all('td', recursive=False)
        for i in range(0, len(cells) - 1, 2):
            key = cells[i].get_text(' ', strip=True).rstrip('：:')
            if key:
                metadata[key] = cells[i + 1].get_text(' ', strip=True)
    if '数据分级' not in metadata:
        raise RuntimeError('未识别到资源详情或开放级别')
    title = s.select_one('.sjxqTit1')
    if not title:
        raise RuntimeError('未识别资源名称')
    return {'source': '温州市数据开放平台', 'id': iid, 'url': r.url, 'title': title.get_text(' ', strip=True), 'metadata': metadata}

def preview(iid):
    d = detail(iid)
    if d['metadata'].get('数据分级') != '完全开放':
        raise ValueError('仅支持详情中确认为完全开放的资源')
    r = requests.post(BASE + 'data_opr/data_pre_list.do', data={'iid': d['id']}, timeout=30, allow_redirects=False)
    r.raise_for_status()
    if r.is_redirect:
        raise RuntimeError('平台重定向，未返回预览')
    try:
        rows = r.json()
    except ValueError as e:
        raise RuntimeError('平台预览非 JSON') from e
    if not isinstance(rows, list) or not rows or (not all((isinstance(row, list) for row in rows))):
        raise RuntimeError('官网预览未返回有效表格')
    d.update({'rows': rows, 'preview_url': BASE + 'detail/data_preview.do?iid=' + d['id'], 'note': '官网预览仅为样本，不代表完整数据；保留原文数值和缺失值。目录更新日不等于数据所属时期。单位、定义须核资源详情或原始统计来源。API 调用另需申请。'})
    return d
