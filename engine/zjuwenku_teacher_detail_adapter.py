"""浙大文库教师著作目录中的单条书目详情。"""
import release_runtime
import re
from urllib.parse import urlencode
from urllib.request import urlopen
from bs4 import BeautifulSoup
from zjuwenku_api import BASE

def teacher_detail(record_id):
    if not isinstance(record_id, str) or not re.fullmatch('[0-9a-fA-F]{32}', record_id):
        raise ValueError('书目编号须为32位十六进制')
    record_id = record_id.lower()
    url = BASE + 'book/teacher/detail?' + urlencode({'id': record_id})
    with urlopen(url, timeout=20) as response:
        soup = BeautifulSoup(response.read().decode('utf-8'), 'html.parser')
    table = soup.select_one('table.m-table-c2')
    if not table:
        raise RuntimeError('未识别教师著作书目详情')
    fields = []
    for cell in table.select('th,td'):
        label, separator, value = cell.get_text(' ', strip=True).partition('：')
        if separator and label:
            fields.append({'label': label, 'value': value})
    if not any((f['label'] == '题名' and f['value'] for f in fields)):
        raise RuntimeError('教师著作书目缺少题名')
    return {'source': '浙大文库教师著作书目', 'id': record_id, 'record_url': url, 'fields': fields, 'note': '仅教师著作基本题录，不含简介、图片或全文；上游使用 HTTP。'}
