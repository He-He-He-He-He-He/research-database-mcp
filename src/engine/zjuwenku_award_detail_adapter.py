"""浙大文库获奖作品页面的公开书目与获奖字段。"""
import release_runtime
import re
from urllib.parse import urlencode
from urllib.request import urlopen
from bs4 import BeautifulSoup
from zjuwenku_api import BASE

def award_detail(record_id):
    if not isinstance(record_id, str) or not re.fullmatch('[0-9a-fA-F]{32}', record_id):
        raise ValueError('记录编号须为32位十六进制')
    record_id = record_id.lower()
    url = BASE + 'award/detail?' + urlencode({'id': record_id})
    with urlopen(url, timeout=20) as response:
        soup = BeautifulSoup(response.read().decode('utf-8'), 'html.parser')
    table = soup.select_one('table.m-table-c2')
    if not table:
        raise RuntimeError('未识别获奖作品详情')
    fields = []
    for cell in table.select('th,td'):
        label, sep, value = cell.get_text(' ', strip=True).partition('：')
        if sep and label:
            fields.append({'label': label, 'value': value})
    if not any((f['label'] == '题名' and f['value'] for f in fields)):
        raise RuntimeError('获奖作品详情缺少题名')
    return {'source': '浙大文库获奖作品', 'id': record_id, 'record_url': url, 'fields': fields, 'note': '返回页面书目及获奖字段；不含全文或图片，获奖名称若页面未列出不自行推断。上游 HTTP。'}
