"""浙大文库求是学人页面上的作品书目表。"""
import release_runtime
import re
from urllib.parse import urlencode
from urllib.request import urlopen
from bs4 import BeautifulSoup
from zjuwenku_api import BASE

def works(record_id):
    if not isinstance(record_id, str) or not re.fullmatch('[0-9a-fA-F]{32}', record_id):
        raise ValueError('人物编号须为32位十六进制')
    record_id = record_id.lower()
    url = BASE + 'people/detail?' + urlencode({'type': '0', 'id': record_id})
    with urlopen(url, timeout=20) as r:
        soup = BeautifulSoup(r.read().decode('utf-8'), 'html.parser')
    profile = soup.select_one('table.m-table-c2')
    tables = soup.select('table.m-table:not(.m-table-c2)')
    if not soup.title or '求是学人信息' not in soup.title.get_text() or (not profile) or (len(tables) != 1):
        raise RuntimeError('未识别求是学人及其作品表')
    profile_text = profile.get_text(' ', strip=True)
    m = re.search('姓名：\\s*(.*?)\\s*学科：', profile_text, re.S)
    if not m or not m.group(1):
        raise RuntimeError('人物姓名缺失')
    table = tables[0]
    heads = [x.get_text(' ', strip=True) for x in table.select('thead th')]
    if heads != ['题名', '著者', '出版者', 'ISBN', '获奖情况(索书号对应)']:
        raise RuntimeError('作品表列名发生变化')
    items = []
    for row in table.select('tbody tr'):
        cells = row.find_all('td', recursive=False)
        if len(cells) != 5:
            raise RuntimeError('作品表列数异常')
        item = dict(zip(heads, [x.get_text(' ', strip=True) for x in cells]))
        match = re.fullmatch("toDetail\\('([0-9a-fA-F]{32})'\\);?", cells[0].get('onclick', '').strip())
        if not match:
            raise RuntimeError('作品编号未识别')
        item['id'] = match.group(1)
        items.append(item)
    return {'source': '浙大文库求是学人作品表', 'id': record_id, 'person': m.group(1).strip(), 'record_url': url, 'columns': heads, 'items': items, 'note': '仅人物页面当前显示的作品表，原始空值保留；非完整著作目录，不代表全文或获奖信息完整。上游 HTTP。'}
