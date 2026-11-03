"""浙大文库求是学人作品详情。"""
import release_runtime
import re
from urllib.parse import urlencode
from urllib.request import urlopen
from bs4 import BeautifulSoup
from zjuwenku_api import BASE

def book_detail(record_id):
    if not isinstance(record_id, str) or not re.fullmatch('[0-9a-fA-F]{32}', record_id):
        raise ValueError('作品编号须为32位十六进制')
    record_id = record_id.lower()
    url = BASE + 'people/bookdetail?' + urlencode({'id': record_id})
    with urlopen(url, timeout=20) as r:
        soup = BeautifulSoup(r.read().decode('utf-8'), 'html.parser')
    table = soup.select_one('table.m-table-c2')
    if not table or not soup.title or '著作详情-求是学人' not in soup.title.get_text():
        raise RuntimeError('未识别求是学人作品详情')
    fields = []
    for cell in table.select('th,td'):
        k, sep, v = cell.get_text(' ', strip=True).partition('：')
        if sep and k:
            fields.append({'label': k, 'value': v.strip()})
    if not any((x['label'] == '题名' and x['value'] for x in fields)):
        raise RuntimeError('书目题名缺失')
    return {'source': '浙大文库求是学人作品详情', 'id': record_id, 'record_url': url, 'fields': fields, 'note': '仅页面书目基本字段，不含简介、全文或图片；上游 HTTP。'}
