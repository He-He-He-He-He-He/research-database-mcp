"""浙大文库求是学人公开页面的基本字段。"""
import release_runtime
import re
from urllib.parse import urlencode
from urllib.request import urlopen
from bs4 import BeautifulSoup
from zjuwenku_api import BASE

def person_detail(record_id):
    if not isinstance(record_id, str) or not re.fullmatch('[0-9a-fA-F]{32}', record_id):
        raise ValueError('人物编号须为32位十六进制')
    record_id = record_id.lower()
    url = BASE + 'people/detail?' + urlencode({'type': '0', 'id': record_id})
    with urlopen(url, timeout=20) as response:
        soup = BeautifulSoup(response.read().decode('utf-8'), 'html.parser')
    table = soup.select_one('table.m-table-c2')
    if not table or not soup.title or '求是学人信息' not in soup.title.get_text():
        raise RuntimeError('未识别求是学人页面')
    fields = []
    for cell in table.select('th,td'):
        text = cell.get_text(' ', strip=True)
        match = re.fullmatch('\\s*姓名：\\s*(.*?)\\s*学科：\\s*(.*?)\\s*出生年：\\s*(.*?)\\s*', text, re.S)
        if match:
            fields.extend(({'label': label, 'value': value.strip()} for label, value in zip(('姓名', '学科', '出生年'), match.groups())))
    if not any((f['label'] == '姓名' and f['value'] for f in fields)):
        raise RuntimeError('人物页面缺少姓名')
    return {'source': '浙大文库求是学人', 'id': record_id, 'record_url': url, 'fields': fields, 'note': '仅求是学人（type=0）页面基本字段，不含人物正文、图片或作品表；空值保留。上游 HTTP。'}
